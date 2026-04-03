import { defineStore } from 'pinia'

import { v4 as uuidv4 } from 'uuid'

import { ref, type Ref, computed, watch, onMounted } from 'vue'
import { useTitle } from '@vueuse/core'

import { usePlayer } from '@/composables/Player'
import { useCharacter } from '@/composables/Character'
import { useEntity } from '@/composables/Entity'

import type { Entity, Location, Player } from '@/interfaces/Types'

export enum input_methods {
	// Keyboard = 'keyboard',
	// Mouse = 'mouse',
	kbm = 'mouse',
	touch = 'touch/touchpad',
	// Pen = 'pen',
	// Voice = 'voice'
}

export const usePlayerStore = defineStore(
	'player',
	() => {
		const mounted = ref(false)
		//	player variables
		const uuid: Ref<string> = ref('')
		const player_id = ref<string>("")
		const {
			player,
			set_player_id,
			retrieve_player,
			activate_entity
		} = usePlayer(undefined, player_id.value)
		const player_name: Ref<string> = ref("")
		const is_player = computed(() => !is_gm.value)

		function switch_player(player: Player) {
			if(player.id) {
				player_id.value = player.id
				set_player_id(player.id)
				retrieve_player()
			}
		}

		//	character, important to store separately for cookie
		const player_character_key: Ref<string|undefined> = ref()
		const player_character_id: Ref<string|undefined> = ref()
		const previous_perspective_ids: Ref<Array<string>> = ref([])

		// const 
		const plot_points: Ref<number> = ref(0)
		const is_active_player: Ref<boolean> = ref(false)
		const small_buttons: Ref<boolean> = ref(false)
		const data_saving: Ref<boolean> = ref(false)
		const traitset_defaults: Ref<string> = ref("EXPANDED") // COLLAPSED, ACTIVE, EXPANDED
		const tickets_remaining: Ref<number> = ref(20)

		//	GM variables
		const is_gm: Ref<boolean> = ref(false)

		//	session variables
		const session_id: Ref<string> = ref("")
		const scene_id: Ref<string> = ref("")
		const beat_id: Ref<string> = ref("")
		const active_location = computed(() => player_character.value?.location?.id ?? "Entities/2")
		const editing = ref(false)
		const viewing = ref(false)

		const orientation = ref("horizontal")	// horizontal (for landscape, e.g. desktop monitor) or vertical (for portrait, e.g. mobile)
		const theme = ref("dark")
		const font_size = ref(16)
		const input_method = ref<input_methods|undefined>()

		const image_entity = ref<Entity|undefined>(undefined)


		const location_update_counter = ref<number>(0)

		// const {
		// 	character: player_character,
		// 	retrieve_character,
		// 	retrieve_relations,
		// 	set_character_key,
		// 	set_location
		// } = useCharacter(undefined, player_character_key?.value)
		
		// watch(player_character_key, (newCharacterKey) => {
		// 	if(newCharacterKey && !is_gm.value) {
		// 		set_character_key(newCharacterKey)
		// 	}
		// })

		const {
			entity: player_character,
			set_entity_id: set_player_character_id,
			retrieve_full_entity: retrieve_character,
			retrieve_relations: retrieve_character_relations,
			create_relation: create_character_relation,
			set_location: set_character_location,
		} = useEntity(undefined, player_character_id.value)

		function set_character_id(id: string) {
			player_character_id.value = id
			set_player_character_id(id)
		}

		function save_perspective_id(new_perspective_id: string) {
			if(!new_perspective_id) return
			const existingIndex = previous_perspective_ids.value.indexOf(new_perspective_id)
			if(existingIndex > -1) {
				previous_perspective_ids.value.splice(existingIndex, 1)
			}
			previous_perspective_ids.value.unshift(new_perspective_id)
			previous_perspective_ids.value = Array.from(new Set(previous_perspective_ids.value)).slice(0, 13)
		}

		watch(player_character, (newCharacter) => {
			if(!newCharacter.active) {
				activate_entity(newCharacter.id)
			}
		})

		const perspective_id = ref<string>('Entities/1')
		const {
			entity: perspective,
			set_entity_id: set_perspective_id,
			retrieve_full_entity: retrieve_perspective,
			retrieve_relations: retrieve_perspective_relations,
			create_relation: create_perspective_relation,
			delete_relation: delete_perspective_relation,
			set_location: set_perspective_location,
			set_archetype: set_perspective_archetype,
			unset_archetype: unset_perspective_archetype,
			set_entity_location,
			deactivate_entity
		} = useEntity(undefined, perspective_id.value)

		async function set_perspective(new_perspective_id: string) {
			console.log("setting perspective to " + new_perspective_id)
			if(perspective_id.value != new_perspective_id) {
				console.log("deactivating perspective ", perspective_id.value)
				deactivate_entity(perspective_id.value)
			}
			perspective_id.value = new_perspective_id
			set_perspective_id(new_perspective_id)
			activate_entity(perspective_id.value)
			if(new_perspective_id == "Entities/1" && perspective.value.location) {
				await set_entity_location(new_perspective_id, perspective.value.location.id)
				await retrieve_perspective()
			}
			else {
				await retrieve_perspective()
			}
		}

		// watch(() => perspective.value.id, (newPerspectiveId) => {
		// 	perspective_id.value = newPerspectiveId
		// })

		const the_entity = computed(() => {
			if(!is_gm.value && player_character.value) {
				return player_character.value
			}
			else if(is_gm.value && perspective.value) {
				return perspective.value
			}
		})

		// watch(() => the_entity.value, (newEntity, oldEntity) => {
		// 	console.log("the entity changed from " + oldEntity?.name + " to " + newEntity?.name)

		// 	if(newEntity?.location && oldEntity && oldEntity.location && newEntity.location.id != oldEntity.location.id) {
		// 		//	update the title to the location when transversing
		// 		console.log("Changing title from " + oldEntity?.location?.name + " to " + newEntity.location.name)
		// 		useTitle(newEntity.location.name)
		// 	}

		// 	if(newEntity && newEntity.id == 'Entities/1' && oldEntity && newEntity.id != oldEntity.id && oldEntity.location) {
		// 		//	set GM location to where the user left off
		// 		console.log("Setting GM location to " + oldEntity.location.name)
		// 		set_perspective_location(oldEntity.location)
		// 	}
		// 	if(newEntity && newEntity.id == perspective_id.value && oldEntity && newEntity.id != oldEntity.id) {
		// 		console.log("switching from " + oldEntity.name + " (" + oldEntity.id + ") to " + newEntity.name + " (" + newEntity.id + ")")
		// 		if(oldEntity?.id && oldEntity.id != 'placeholder') {
		// 			deactivate_entity(oldEntity.id)
		// 			save_perspective_id(oldEntity.id)
		// 		}
		// 		if(newEntity && is_gm.value) {
		// 			// activate_perspective()
		// 			activate_entity(newEntity)
		// 		}
		// 	}
		// })
		
		// switching between gm and player
		watch(is_gm, (newIsGm, oldIsGm) => {
			if(newIsGm != oldIsGm && mounted.value) {
				console.log("GM changed from " + oldIsGm + " to " + newIsGm)

				//	retrieve the entity when switching between gm and player
				if(perspective_id.value && perspective.value.id != perspective_id.value && newIsGm) {
					console.warn("changing perspective from " + perspective.value.id + " to " + perspective_id.value)
					set_perspective_id(perspective_id.value)
					// retrieve_perspective()
				}
				if(player_character_id.value && !newIsGm) {
					console.log("retrieving character of " + player_character_id.value)
					set_character_id(player_character_id.value)
					retrieve_character()
				}

				// players don't have an editing mode, so auto switch off when switching to player
				if(!newIsGm) {
					if(editing.value) {
						editing.value = false
					}
				}
			}
		})

		const playing = ref(true)

		function create_player() {
			if(!uuid.value) {
				uuid.value = uuidv4()
			}
		}

		// function retrieve_the_entity() {
		// 	if(perspective_id.value && perspective.value.id != perspective_id.value && is_gm.value) {
		// 		console.log("retrieving perspective, from " + perspective.value.id + " to " + perspective_id.value)
		// 		set_perspective_id(perspective_id.value)
		// 		retrieve_perspective()
		// 	}
		// 	if(player_character_key.value && player_character.value.key != player_character_key.value && !is_gm.value) {
		// 		console.log("retrieving character")
		// 		set_character_key(player_character_key.value)
		// 		retrieve_character()
		// 	}
		// }

		onMounted(() => {
			mounted.value = true
			// retrieve_the_entity()
			if(player_id.value) {
				console.log("retrieving player " + player_id.value)
				set_player_id(player_id.value)
				retrieve_player()
			}
			if(perspective_id.value) {
				console.log("retrieving perspective " + perspective_id.value)
				set_perspective(perspective_id.value)
				// retrieve_perspective()
			}
			if(player_character_id.value) {
				console.log("retrieving character " + player_character_id.value)
				set_character_id(player_character_id.value)
				retrieve_character()
			}
		})

		return {
			uuid,
			player_id,
			player_name,
			player,
			switch_player,
			retrieve_player,
			is_player,
			small_buttons,
			data_saving,
			image_entity,
			traitset_defaults,
			player_character,
			player_character_key,
			previous_perspective_ids,
			player_character_id,
			retrieve_character,
			retrieve_character_relations,
			create_character_relation,
			set_character_location,
			set_character_id,
			perspective_id,
			set_perspective,
			perspective,
			retrieve_perspective,
			retrieve_perspective_relations,
			create_perspective_relation,
			delete_perspective_relation,
			set_perspective_location,
			set_perspective_archetype,
			unset_perspective_archetype,
			the_entity,
			// retrieve_the_entity,
			plot_points,
			is_active_player,
			is_gm,
			playing,
			session_id,
			scene_id,
			beat_id,
			active_location,
			create_player,
			editing,
			viewing,
			orientation,
			theme,
			font_size,
			input_method,
			tickets_remaining,
			location_update_counter
		}
	},
	{
		// https://github.com/prazdevs/pinia-plugin-persistedstate
		persist: {
			debug: true,
			paths: [
				'uuid',
				'player_id',
				'player_name', 
				'player_character_key',
				'player_character_id',
				// 'player_character',
				'previous_perspective_ids',
				'perspective_id', 
				// 'perspective',
				'is_gm',
				'playing',
				'small_buttons',
				'data_saving',
				'traitset_defaults',
				'tickets_remaining',
				'font_size',
				'input_method'
			],
		},
	},
)
