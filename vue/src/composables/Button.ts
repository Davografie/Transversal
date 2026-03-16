import { computed } from "vue"

import IconArchetypeAdd from '@/components/icons/IconArchetypeAdd.vue';
import IconArchetypeRemove from '@/components/icons/IconArchetypeRemove.vue';
import IconRelation from "@/components/icons/IconRelation.vue";
import IconSwitch from '@/components/icons/IconSwitch.vue';
import IconGM from "@/components/icons/IconGM.vue";
import IconPP from "@/components/icons/IconPP.vue";
import IconTraitsetsOpen from "@/components/icons/IconTraitsetsOpen.vue";
import IconTraitsetsActive from "@/components/icons/IconTraitsetsActive.vue";
import IconTraitsetsClosed from "@/components/icons/IconTraitsetsClosed.vue";
import IconScaling from "@/components/icons/IconScaling.vue";
import IconKnownTo from "@/components/icons/IconKnownTo.vue";
import IconTrash from "@/components/icons/IconTrash.vue";
import IconSettings from "@/components/icons/IconSettings.vue";

export enum ButtonTypes {
	ADD_ARCHETYPE = 'add_archetype',
	REMOVE_ARCHETYPE = 'delete_archetype',
	RELATION = 'relation',
	SWITCH = 'switch',
	GM = 'gm',
	PP = 'pp',
	TRAITSET_OPEN = 'traitset_open',
	TRAITSET_ACTIVE = 'traitset_active',
	TRAITSET_CLOSED = 'traitset_closed',
	SCALING = 'scaling',
	KNOWN_TO = 'known_to',
	TRASH = 'trash',
	SETTINGS = 'settings'
}

export function useButtonTypes(_type: ButtonTypes) {
	const label = computed(() => {
		switch (_type) {
			case ButtonTypes.ADD_ARCHETYPE:
				return 'add archetype';
			case ButtonTypes.REMOVE_ARCHETYPE:
				return 'remove archetype';
			case ButtonTypes.RELATION:
				return 'relation';
			case ButtonTypes.SWITCH:
				return 'switch entities';
			case ButtonTypes.GM:
				return 'gm';
			case ButtonTypes.PP:
				return 'plot point';
			case ButtonTypes.TRAITSET_OPEN:
				return 'open';
			case ButtonTypes.TRAITSET_ACTIVE:
				return 'active';
			case ButtonTypes.TRAITSET_CLOSED:
				return 'closed';
			case ButtonTypes.SCALING:
				return 'scaling';
			case ButtonTypes.KNOWN_TO:
				return 'known to';
			case ButtonTypes.TRASH:
				return 'trash';
			case ButtonTypes.SETTINGS:
				return 'settings';
			default:
				return '';
		}
	})
	const the_component = computed(() => {
		switch(_type) {
			case ButtonTypes.ADD_ARCHETYPE:
				return IconArchetypeAdd
			case ButtonTypes.REMOVE_ARCHETYPE:
				return IconArchetypeRemove
			case ButtonTypes.RELATION:
				return IconRelation
			case ButtonTypes.SWITCH:
				return IconSwitch
			case ButtonTypes.GM:
				return IconGM
			case ButtonTypes.PP:
				return IconPP
			case ButtonTypes.TRAITSET_OPEN:
				return IconTraitsetsOpen
			case ButtonTypes.TRAITSET_ACTIVE:
				return IconTraitsetsActive
			case ButtonTypes.TRAITSET_CLOSED:
				return IconTraitsetsClosed
			case ButtonTypes.SCALING:
				return IconScaling
			case ButtonTypes.KNOWN_TO:
				return IconKnownTo
			case ButtonTypes.TRASH:
				return IconTrash
			case ButtonTypes.SETTINGS:
				return IconSettings
		}
	})
	return {
		ButtonTypes,
		label,
		the_component
	}
}
