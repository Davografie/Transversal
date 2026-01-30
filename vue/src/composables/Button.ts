import { computed } from "vue"

import IconAddArchetype from '@/components/icons/IconAddArchetype.vue';
import IconSwitch from '@/components/icons/IconSwitch.vue';
import IconGM from "@/components/icons/IconGM.vue";
import IconPP from "@/components/icons/IconPP.vue";
import IconTraitsetsOpen from "@/components/icons/IconTraitsetsOpen.vue";
import IconTraitsetsActive from "@/components/icons/IconTraitsetsActive.vue";
import IconTraitsetsClosed from "@/components/icons/IconTraitsetsClosed.vue";
import IconScaling from "@/components/icons/IconScaling.vue";
import IconKnownTo from "@/components/icons/IconKnownTo.vue";
import IconTrash from "@/components/icons/IconTrash.vue";

export enum ButtonTypes {
	ADD_ARCHETYPE = 'add_archetype',
	SWITCH = 'switch',
	GM = 'gm',
	PP = 'pp',
	TRAITSET_OPEN = 'traitset_open',
	TRAITSET_ACTIVE = 'traitset_active',
	TRAITSET_CLOSED = 'traitset_closed',
	SCALING = 'scaling',
	KNOWN_TO = 'known_to',
	TRASH = 'trash'
}

export function useButtonTypes(_type: ButtonTypes) {
	const label = computed(() => {
		switch (_type) {
			case ButtonTypes.ADD_ARCHETYPE:
				return 'add archetype';
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
			default:
				return '';
		}
	})
	const the_component = computed(() => {
		switch(_type) {
			case ButtonTypes.ADD_ARCHETYPE:
				return IconAddArchetype
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
		}
	})
	return {
		ButtonTypes,
		label,
		the_component
	}
}
