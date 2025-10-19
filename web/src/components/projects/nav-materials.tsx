import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuAction,
} from '@/components/ui/sidebar'
import { MoreHorizontal, BrainCircuit, ListChecks } from 'lucide-react'
import { truncate } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import type { Material } from '@/integrations/api'

type Props = React.ComponentProps<typeof SidebarGroup> & {
  materials: Material[]
  onSelectMaterialId?: (materialId: string) => void
}

const getMaterialIcon = (type: Material['type']) => {
  switch (type) {
    case 'flashcard_group':
      return <BrainCircuit className="size-4" />
    case 'quiz':
      return <ListChecks className="size-4" />
  }
}

const getMaterialName = (material: Material) => {
  if (material.type === 'flashcard_group') {
    return material.name
  }
  return material.name
}

export const NavMaterials = ({
  materials,
  onSelectMaterialId,
  ...props
}: Props) => {
  return (
    <SidebarGroup {...props}>
      <SidebarGroupLabel>Materials</SidebarGroupLabel>

      <SidebarGroupContent>
        <SidebarMenu>
          {materials.map((material) => (
            <SidebarMenuItem key={material.id}>
              <SidebarMenuButton
                tooltip={getMaterialName(material)}
                onClick={() => onSelectMaterialId?.(material.id)}
              >
                {getMaterialIcon(material.type)}
                {truncate(getMaterialName(material), 20)}
              </SidebarMenuButton>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuAction>
                    <MoreHorizontal />
                  </SidebarMenuAction>
                </DropdownMenuTrigger>
                <DropdownMenuContent side="right" align="start">
                  <DropdownMenuItem variant="destructive">
                    <span>Delete {material.type === 'flashcard_group' ? 'Flashcard' : 'Quiz'}</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
