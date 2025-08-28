import { defineStore } from 'pinia'

import { v4 as uuidv4 } from 'uuid'

import { ref, type Ref, computed, watch, onMounted } from 'vue'
import { useTitle } from '@vueuse/core'

import { useCharacter } from '@/composables/Character'
import { useEntity } from '@/composables/Entity'

import type { Location } from '@/interfaces/Types'

export const usePlayer = defineStore(
	'player',
	() => {
		const mounted = ref(false)
		//	player variables
		const uuid: Ref<string> = ref('')
		const player_name: Ref<string> = ref("")
		const is_player = computed(() => !is_gm.value)

		//	character
		const player_character_key: Ref<string|undefined> = ref()

		// const 
		const plot_points: Ref<number> = ref(0)
		const is_active_player: Ref<boolean> = ref(false)
		const small_buttons: Ref<boolean> = ref(false)
		const data_saving: Ref<boolean> = ref(false)
		const traitset_defaults: Ref<string> = ref("ACTIVE") // COLLAPSED, ACTIVE, EXPANDED

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

		const {
			character: player_character,
			retrieve_character,
			retrieve_relations,
			activate_character,
			deactivate_character,
			set_character_key,
			set_location
		} = useCharacter(undefined, player_character_key?.value)
		
		watch(player_character_key, (newCharacterKey) => {
			if(newCharacterKey && !is_gm.value) {
				set_character_key(newCharacterKey)
			}
		})

		watch(player_character, (newCharacter, oldCharacter) => {
			// if(oldCharacter) {
			// 	deactivate_character()
			// }
			if(!newCharacter.active) {
				activate_character(uuid.value)
			}
		})

		const perspective_id = ref<string>('Entities/1')
		const {
			entity: perspective,
			set_entity_id: set_perspective_id,
			retrieve_entity: retrieve_perspective,
			retrieve_relations: retrieve_perspective_relations,
			set_location: set_perspective_location,
			activate_entity: activate_perspective,
			deactivate_entity
		} = useEntity(undefined, perspective_id.value)

		watch(() => perspective.value.id, (newPerspectiveId) => {
			perspective_id.value = newPerspectiveId
		})

		const the_entity = computed(() => {
			if(!is_gm.value && player_character.value) {
				return player_character.value
			}
			else if(is_gm.value && perspective.value) {
				return perspective.value
			}
		})

		watch(() => the_entity.value, (newEntity, oldEntity) => {
			console.log("the entity changed")

			if(newEntity?.location && oldEntity && oldEntity.location && newEntity.location.id != oldEntity.location.id) {
				//	update the title to the location when transversing
				console.log("Changing title from " + oldEntity?.location?.name + " to " + newEntity.location.name)
				useTitle(newEntity.location.name)
			}

			if(newEntity && newEntity.id == 'Entities/1' && oldEntity && newEntity.id != oldEntity.id && oldEntity.location) {
				//	set GM location to where the user left off
				set_perspective_location(oldEntity.location)
			}
			if(newEntity && oldEntity && newEntity.id != oldEntity.id) {
				console.log("switching from " + oldEntity.name + "/" + oldEntity.key + " to " + newEntity.name + "/" + newEntity.key)
				if(oldEntity && oldEntity.id != 'placeholder') {
					deactivate_entity(oldEntity.key)
				}
				if(newEntity && is_gm.value) {
					activate_perspective()
				}
			}
		})
		
		// switching between gm and player
		watch(is_gm, (newIsGm, oldIsGm) => {
			if(newIsGm != oldIsGm && mounted.value) {
				console.log("gm changed from " + oldIsGm + " to " + newIsGm)

				//	retrieve the entity when switching between gm and player
				if(perspective_id.value && perspective.value.id != perspective_id.value && newIsGm) {
					console.log("changing perspective from " + perspective.value.id + " to " + perspective_id.value)
					set_perspective_id(perspective_id.value)
					retrieve_perspective()
				}
				if(player_character_key.value && !newIsGm) {
					console.log("retrieving character of " + player_character_key.value)
					set_character_key(player_character_key.value)
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

		function create_player() {
			if(!uuid.value) {
				uuid.value = uuidv4()
			}
		}

		function retrieve_the_entity() {
			if(perspective_id.value && perspective.value.id != perspective_id.value && is_gm.value) {
				console.log("retrieving perspective")
				set_perspective_id(perspective_id.value)
				retrieve_perspective()
			}
			if(player_character_key.value && player_character.value.key != player_character_key.value && !is_gm.value) {
				console.log("retrieving character")
				set_character_key(player_character_key.value)
				retrieve_character()
			}
		}

		onMounted(() => {
			mounted.value = true
			retrieve_the_entity()
		})

		return {
			uuid,
			player_name,
			is_player,
			small_buttons,
			data_saving,
			traitset_defaults,
			player_character,
			player_character_key,
			retrieve_character,
			retrieve_relations,
			set_location,
			perspective_id,
			set_perspective_id,
			perspective,
			retrieve_perspective,
			retrieve_perspective_relations,
			set_perspective_location,
			the_entity,
			retrieve_the_entity,
			plot_points,
			is_active_player,
			is_gm,
			session_id,
			scene_id,
			beat_id,
			active_location,
			create_player,
			editing,
			viewing,
			orientation,
			theme
		}
	},
	{
		// https://github.com/prazdevs/pinia-plugin-persistedstate
		persist: {
			debug: true,
			paths: ['uuid', 'player_name', 'player_character_key', 'perspective_id', 'is_gm', 'small_buttons', 'data_saving'],
		},
	},
)
