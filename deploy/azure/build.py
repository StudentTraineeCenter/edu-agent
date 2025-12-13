#!/usr/bin/env python3
"""
ACR Build Script

Builds and pushes container images to Azure Container Registry using ACR Tasks.
ACR Tasks perform remote builds, so no local Docker installation is required.

Usage:
    python build.py                          # Build all containers
    python build.py --container edu-api      # Build specific container
    python build.py --acr-name myacr         # Specify ACR name directly
    python build.py --list                   # List available containers
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path

import yaml


def get_script_dir() -> Path:
    """Get the directory containing this script."""
    return Path(__file__).parent.resolve()


def load_config(config_path: Path) -> dict:
    """Load build configuration from YAML file."""
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_acr_name_from_terraform(terraform_dir: Path) -> str | None:
    """Get ACR name from Terraform output."""
    try:
        result = subprocess.run(
            ["terraform", "output", "-raw", "acr_name"],
            cwd=terraform_dir,
            capture_output=True,
            text=True,
            check=True,
            shell=True,  # Required on Windows
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        print("Warning: terraform not found in PATH", file=sys.stderr)
        return None


def get_terraform_output(terraform_dir: Path, output_name: str) -> str | None:
    """Get a terraform output value."""
    try:
        is_windows = platform.system() == "Windows"
        result = subprocess.run(
            ["terraform", "output", "-raw", output_name],
            cwd=terraform_dir,
            capture_output=True,
            text=True,
            check=True,
            shell=is_windows,  # Only use shell on Windows
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        return None


def resolve_build_args(build_args: dict, terraform_dir: Path) -> dict:
    """Resolve build args from terraform outputs if empty.
    
    Maps build arg names to terraform output names:
    - VITE_SERVER_URL -> container_app_api_url (with https:// prefix)
    - VITE_SUPABASE_URL -> supabase_api_url
    - VITE_SUPABASE_ANON_KEY -> from variable (needs to be set manually)
    """
    resolved = {}
    
    # Mapping of build arg names to terraform output names
    terraform_mapping = {
        "VITE_AZURE_ENTRA_TENANT_ID": "azure_tenant_id",
        "VITE_SERVER_URL": "container_app_api_url",
        "VITE_SUPABASE_URL": "supabase_api_url",
    }
    
    for key, value in build_args.items():
        if value and value.strip():  # Already has a value
            resolved[key] = value
        elif key in terraform_mapping:
            # Try to get from terraform
            tf_output = get_terraform_output(terraform_dir, terraform_mapping[key])
            if tf_output:
                # Add https:// prefix for URLs if needed
                if key == "VITE_SERVER_URL" and not tf_output.startswith("http"):
                    resolved[key] = f"https://{tf_output}"
                else:
                    resolved[key] = tf_output
            else:
                resolved[key] = ""  # Keep empty if not found
        else:
            resolved[key] = value  # Keep original value (empty or otherwise)
    
    return resolved


def build_container(acr_name: str, container: dict, base_path: Path, terraform_dir: Path | None = None) -> bool:
    """Build and push a container using ACR Tasks.
    
    Args:
        acr_name: Azure Container Registry name
        container: Container configuration dict
        base_path: Base path for resolving relative paths
        terraform_dir: Optional terraform directory for resolving build args
        
    Returns:
        True if build succeeded, False otherwise
    """
    name = container["name"]
    image = container["image"]
    tag = container.get("tag", "latest")
    if container["path"] == "src/":
        context_path = (base_path / "src").resolve()
    else:
        context_path = (base_path / container["path"]).resolve()
    dockerfile_rel = container.get("dockerfile", "Dockerfile")
    
    if not context_path.exists():
        print(f"Error: Build context not found: {context_path}", file=sys.stderr)
        return False
    
    # Check for Dockerfile - if dockerfile path contains '/', it's relative to project root, not context
    if '/' in dockerfile_rel:
        dockerfile = (base_path / dockerfile_rel).resolve()
    else:
        dockerfile = context_path / dockerfile_rel
    
    if not dockerfile.exists():
        print(f"Error: Dockerfile not found: {dockerfile}", file=sys.stderr)
        return False
    
    # Compute dockerfile path relative to base_path for --file argument
    # az acr build expects --file to be relative to the working directory (base_path)
    dockerfile_for_cmd = str(dockerfile.relative_to(base_path))
    
    # Compute context path relative to base_path for build context argument
    # az acr build expects the context to be relative to the working directory (base_path)
    context_for_cmd = str(context_path.relative_to(base_path))
    
    full_image = f"{image}:{tag}"
    print(f"\n{'='*60}")
    print(f"Building: {name}")
    print(f"  Image: {acr_name}.azurecr.io/{full_image}")
    print(f"  Context: {context_path}")
    print(f"  Dockerfile: {dockerfile_for_cmd}")
    
    # Resolve build args from terraform if needed
    build_args = container.get("build_args", {})
    if build_args and terraform_dir and terraform_dir.exists():
        print(f"Resolving build args from terraform outputs...")
        build_args = resolve_build_args(build_args, terraform_dir)
    
    # Validate required build args are present (non-empty)
    if build_args:
        missing = [key for key, value in build_args.items() if not value or not value.strip()]
        if missing:
            print(f"Error: Required build args are missing or empty: {', '.join(missing)}", file=sys.stderr)
            print("Please set them in build-config.yaml.", file=sys.stderr)
            # Check which ones can be auto-resolved from terraform
            terraform_mapping = {
                "VITE_SERVER_URL": "container_app_api_url",
                "VITE_SUPABASE_URL": "supabase_api_url",
            }
            auto_resolvable = [key for key in missing if key in terraform_mapping]
            manual_required = [key for key in missing if key not in terraform_mapping]
            if auto_resolvable and terraform_dir and terraform_dir.exists():
                print(f"Note: {', '.join(auto_resolvable)} can be auto-resolved from terraform outputs.", file=sys.stderr)
            if manual_required:
                print(f"Note: {', '.join(manual_required)} must be set manually (not available as terraform outputs).", file=sys.stderr)
            return False
        
        print(f"  Build args: {', '.join(build_args.keys())}")
    print(f"{'='*60}\n")
    
    cmd = [
        "az", "acr", "build",
        "--registry", acr_name,
        "--image", full_image,
        "--file", dockerfile_for_cmd,
        context_for_cmd,
        "--debug"
    ]
    
    # Add build args to command (only non-empty values)
    for key, value in build_args.items():
        if value and value.strip():  # Only add non-empty build args
            cmd.extend(["--build-arg", f"{key}={value}"])

    try:
        # On Windows, shell=True is needed to find az.cmd, but we need to pass as string
        # On Unix, shell=False works correctly with list arguments
        is_windows = platform.system() == "Windows"
        if is_windows:
            # Convert list to string for Windows shell
            cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd)
            result = subprocess.run(cmd_str, check=True, shell=True, cwd=base_path, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, check=True, shell=False, cwd=base_path, capture_output=True, text=True)
        print(f"\n✓ Successfully built {name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to build {name}: {e}", file=sys.stderr)
        if e.stdout:
            print("STDOUT:", file=sys.stderr)
            print(e.stdout, file=sys.stderr)
        if e.stderr:
            print("STDERR:", file=sys.stderr)
            print(e.stderr, file=sys.stderr)
        return False


def list_containers(config: dict) -> None:
    """List available containers from config."""
    print("\nAvailable containers:")
    print("-" * 40)
    for container in config.get("containers", []):
        name = container["name"]
        image = container["image"]
        tag = container.get("tag", "latest")
        path = container["path"]
        dockerfile = container.get("dockerfile")
        print(f"  {name}")
        print(f"    Image: {image}:{tag}")
        print(f"    Path:  {path}")
        if dockerfile:
            print(f"    Dockerfile: {dockerfile}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Build container images using Azure Container Registry Tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python build.py                          # Build all containers
    python build.py --container edu-api      # Build specific container
    python build.py --acr-name myacr         # Specify ACR name directly
    python build.py --list                   # List available containers
        """,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to build config YAML (default: build-config.yaml in script directory)",
    )
    parser.add_argument(
        "--acr-name",
        dest="acr_name",
        help="Azure Container Registry name (auto-detected from Terraform if not specified)",
    )
    parser.add_argument(
        "--container", "-c",
        dest="containers",
        action="append",
        help="Specific container to build (can be specified multiple times)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available containers and exit",
    )
    
    args = parser.parse_args()
    
    # Determine paths
    script_dir = get_script_dir()
    config_path = args.config or (script_dir / "build-config.yaml")
    terraform_dir = script_dir / "terraform"
    # Project root is 2 levels up from deploy/azure/
    project_root = script_dir.parent.parent
    
    # Load configuration
    config = load_config(config_path)
    
    # Handle --list
    if args.list:
        list_containers(config)
        return
    
    # Determine ACR name
    acr_name = args.acr_name or config.get("acr_name")
    if not acr_name:
        print("Detecting ACR name from Terraform output...")
        acr_name = get_acr_name_from_terraform(terraform_dir)
    
    if not acr_name:
        print(
            "Error: ACR name not specified and could not be detected from Terraform.\n"
            "Please specify --acr-name or run 'terraform apply' first.",
            file=sys.stderr,
        )
        sys.exit(1)
    
    print(f"Using ACR: {acr_name}")
    
    # Determine which containers to build
    all_containers = config.get("containers", [])
    if not all_containers:
        print("Error: No containers defined in config", file=sys.stderr)
        sys.exit(1)
    
    if args.containers:
        # Build specific containers
        container_names = set(args.containers)
        containers_to_build = [c for c in all_containers if c["name"] in container_names]
        
        # Check for unknown containers
        known_names = {c["name"] for c in all_containers}
        unknown = container_names - known_names
        if unknown:
            print(f"Error: Unknown containers: {', '.join(unknown)}", file=sys.stderr)
            print(f"Available: {', '.join(known_names)}", file=sys.stderr)
            sys.exit(1)
    else:
        # Build all containers (if enabled in config or no containers specified)
        if config.get("build_all_by_default", True):
            containers_to_build = all_containers
        else:
            print("Error: No containers specified and build_all_by_default is false")
            print("Use --container to specify which containers to build")
            sys.exit(1)
    
    # Build containers
    results = []
    for container in containers_to_build:
        success = build_container(acr_name, container, project_root, terraform_dir)
        results.append((container["name"], success))
    
    # Summary
    print(f"\n{'='*60}")
    print("Build Summary")
    print(f"{'='*60}")
    
    success_count = sum(1 for _, success in results if success)
    fail_count = len(results) - success_count
    
    for name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
    
    print()
    print(f"Total: {len(results)}, Succeeded: {success_count}, Failed: {fail_count}")
    
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
