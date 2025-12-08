import { computed } from "vue"

export enum ButtonTypes {
	ADD_ARCHETYPE = 'add_archetype',
	CANCEL = 'cancel',
	SAVE = 'save',
	EDIT = 'edit',
	REMOVE = 'remove',
	TOGGLE = 'toggle',
	FOLLOW = 'follow',
	UNFOLLOW = 'unfollow',
	FAVORITE = 'favorite',
	UNFAVORITE = 'unfavorite'
}

export function useButtonTypes(_type: ButtonTypes) {
	const label = computed(() => {
		switch (_type) {
			case ButtonTypes.ADD_ARCHETYPE:
				return 'add archetype';
			case ButtonTypes.CANCEL:
				return 'cancel';
			case ButtonTypes.SAVE:
				return 'save';
			case ButtonTypes.EDIT:
				return 'edit';
			case ButtonTypes.REMOVE:
				return 'remove';
			case ButtonTypes.TOGGLE:
				return 'toggle';
			case ButtonTypes.FOLLOW:
				return 'follow';
			case ButtonTypes.UNFOLLOW:
				return 'unfollow';
			case ButtonTypes.FAVORITE:
				return 'favorite';
			case ButtonTypes.UNFAVORITE:
				return 'unfavorite';
			default:
				return '';
		}
	})
	return {
		ButtonTypes,
		label
	}
}
