"""Azure Content Understanding client for document analysis."""

import time
from pathlib import Path

import requests
from requests.models import Response

DEFAULT_API_VERSION = "2025-05-01-preview"
DEFAULT_TIMEOUT_SECONDS = 30


class AzureContentUnderstandingClient:
    """Client for interacting with the Azure Content Understanding service."""

    def __init__(
        self,
        endpoint: str,
        api_version: str = DEFAULT_API_VERSION,
        subscription_key: str = None,
        token_provider: callable = lambda: None,
        x_ms_useragent: str = "data-extraction-code",
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ):
        """Constructor for Azure Content Understanding client.

        Args:
            endpoint: The Azure Content Understanding endpoint URL
            api_version: API version to use (default: 2025-05-01-preview)
            subscription_key: Subscription key for authentication
            token_provider: Optional token provider function
            x_ms_useragent: User agent string
            timeout: Request timeout in seconds

        Raises:
            ValueError: If neither subscription_key nor token_provider is provided,
                or if api_version or endpoint is not provided.
        """
        if not subscription_key and not token_provider:
            raise ValueError(
                "Either subscription key or token provider must be provided."
            )
        if not api_version:
            raise ValueError("API version must be provided.")
        if not endpoint:
            raise ValueError("Endpoint must be provided.")

        self._endpoint = endpoint.rstrip("/")
        self._api_version = api_version
        self._headers = self._get_headers(
            subscription_key, token_provider(), x_ms_useragent
        )
        self._timeout = timeout

    def _get_analyze_url(self, endpoint, api_version, analyzer_id):
        return f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}:analyze?api-version={api_version}"

    def _get_headers(self, subscription_key, api_token, x_ms_useragent):
        """Returns the headers for the HTTP requests.

        Args:
            subscription_key: The subscription key for the service.
            api_token: The API token for the service.
            x_ms_useragent: User agent string.

        Returns:
            dict: A dictionary containing the headers for the HTTP requests.
        """
        headers = (
            {"Ocp-Apim-Subscription-Key": subscription_key}
            if subscription_key
            else {"Authorization": f"Bearer {api_token}"}
        )
        headers["x-ms-useragent"] = x_ms_useragent
        return headers

    def begin_analyze_data(self, analyzer_id: str, data: bytes | dict, **kwargs):
        """Begins the analysis of bytes or dictionary data using the specified analyzer.

        Args:
            analyzer_id: The ID of the analyzer to use.
            data: The data to analyze, either as bytes or a dictionary.
            **kwargs: Additional keyword arguments, such as headers.

        Returns:
            Response: The response from the analysis request.

        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        headers = kwargs.get("headers", {"Content-Type": "application/octet-stream"})
        headers.update(self._headers)
        if isinstance(data, dict):
            response = requests.post(
                url=self._get_analyze_url(
                    self._endpoint, self._api_version, analyzer_id
                ),
                headers=headers,
                json=data,
                timeout=self._timeout,
            )
        else:
            response = requests.post(
                url=self._get_analyze_url(
                    self._endpoint, self._api_version, analyzer_id
                ),
                headers=headers,
                data=data,
                timeout=self._timeout,
            )

        response.raise_for_status()
        return response

    def begin_analyze_file(self, analyzer_id: str, file_location: str):
        """Begins the analysis of a file or URL using the specified analyzer.

        Args:
            analyzer_id: The ID of the analyzer to use.
            file_location: The path to the file or the URL to analyze.

        Returns:
            Response: The response from the analysis request.

        Raises:
            ValueError: If the file location is not a valid path or URL.
            HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        data = None
        if Path(file_location).exists():
            with open(file_location, "rb") as file:
                data = file.read()
            headers = {"Content-Type": "application/octet-stream"}
        elif "https://" in file_location or "http://" in file_location:
            data = {"url": file_location}
            headers = {"Content-Type": "application/json"}
        else:
            raise ValueError("File location must be a valid path or URL.")

        return self.begin_analyze_data(analyzer_id, data, headers=headers)

    def poll_result(
        self,
        response: Response,
        timeout_seconds: int = 180,
        polling_interval_seconds: int = 2,
    ):
        """Polls the result of an asynchronous operation until it completes or times out.

        Args:
            response: The initial response object containing the operation location.
            timeout_seconds: The maximum number of seconds to wait for the operation to complete.
                Defaults to 180.
            polling_interval_seconds: The number of seconds to wait between polling attempts.
                Defaults to 2.

        Raises:
            ValueError: If the operation location is not found in the response headers.
            TimeoutError: If the operation does not complete within the specified timeout.
            RuntimeError: If the operation fails.

        Returns:
            dict: The JSON response of the completed operation if it succeeds.
        """
        operation_location = response.headers.get("operation-location", "")
        if not operation_location:
            raise ValueError("Operation location not found in response headers.")

        headers = {"Content-Type": "application/json"}
        headers.update(self._headers)

        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise TimeoutError(
                    f"Operation timed out after {timeout_seconds:.2f} seconds."
                )

            response = requests.get(
                operation_location, headers=self._headers, timeout=self._timeout
            )
            response.raise_for_status()
            status = response.json().get("status").lower()
            if status == "succeeded":
                return response.json()
            elif status == "failed":
                raise RuntimeError("Request failed.")
            time.sleep(polling_interval_seconds)

