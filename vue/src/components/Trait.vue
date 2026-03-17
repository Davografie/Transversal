<script setup lang="ts">
	import _ from 'lodash'
	import { marked } from 'marked'

	import { ref, type Ref, computed, watch, onMounted } from 'vue'

	import useClipboard from 'vue-clipboard3'

	import { usePreferredColorScheme } from '@vueuse/core'

	const preferredColor = usePreferredColorScheme()

	import { useDicepool } from '@/composables/Dicepool'

	import ButtonMinimal from '@/components/UI/ButtonMinimal.vue'
	import { ButtonTypes } from '@/composables/Button'
	import Rating from '@/components/Rating.vue'
	import RatingEdit from '@/components/RatingEdit.vue'
	// import DiePicker from '@/components/DiePicker.vue'
	import SFX from '@/components/SFX.vue'
	import SubTrait from '@/components/SubTrait.vue'
	import EntityButton from './EntityButton.vue'

	import { usePlayerStore } from '@/stores/PlayerStore'
	
	import { useTrait, view_modes } from '@/composables/Trait'
	import { die_constants, useDie } from '@/composables/Die'
	import { useSFXList } from '@/composables/SFXList'
	import { useLocation } from '@/composables/Location'

	import type {
		Die as DieType,
		SFX as SFXType, Trait,
		Entity as EntityType
	} from '@/interfaces/Types'
	import TraitSelector from './TraitSelector.vue'

	const props = defineProps<{
		trait?: Trait,
		trait_id: string,
		traitset_id?: string,
		traitset_types?: string[],
		trait_setting_id?: string,
		entity_id?: string,
		entity_type?: string,
		entity?: EntityType,
		edit_mode?: boolean,
		viewing?: boolean,
		mode?: view_modes,
		highlight_root_id?: string,
		highlighted?: boolean,
		location_key?: string,
		traitset_limit?: number,
		filter?: string
	}>()

	const emit = defineEmits([
		'refetch',
		'next_traitset',
		'require_traits',
		'set_highlight',
		'kill_highlight',
		'show_trait'
	])

	const player = usePlayerStore()

	const {
		trait,
		retrieve_trait,
		retrieve_trait_setting,
		mutate_trait,
		mutate_trait_setting,
		mutate_trait_setting_temp,
		overwrite_trait,
		copy_trait,
		unassign_trait,
		assign_subtrait,
		unassign_subtrait,
		retrieve_statement_examples,
		retrieve_possible_sfxs,
		change_trait_entity,
		transfer_resource
	} = useTrait(props.trait, props.trait_id, props.trait_setting_id, props.entity_id)
	
	// retrieve_trait()

	onMounted(() => {
		if(trait.value.id == 'placeholder') {
			retrieve_trait().catch((error) => {
				console.error("Error retrieving trait: " + trait.value.id, error)
			})
		}
	})

	const {
		add_die,
		add_complication,
		remove_complication_by_traitsetting,
		check_trait,
		check_subtrait,
		remove_traitsetting_dice,
		inAddingPhase,
		traitset_dice,
		change_result_limit
	} = useDicepool(false)

	const {
		location,
		set_location_key,
		retrieve_location,
		retrieve_presence,
		retrieve_parents
	} = useLocation(undefined, props.location_key)

	const { toClipboard } = useClipboard()
	const copy_id = async () => {
		try {
			await toClipboard(trait.value.traitSettingId ?? trait.value.id)
			console.log('Copied to clipboard')
		} catch (e) {
			console.error(e)
		}
	}

	// enable/disable trait edit mode
	const mode = ref<view_modes>(props.mode ?? view_modes.Neutral)
	watch(() => props.mode, (newMode) => {
		if(newMode == view_modes.Editing) {
			switch_to_editing()
		}
		mode.value = newMode ?? view_modes.Neutral
	})

	// true for longtaps so that normal taps/clicks don't trigger
	const held = ref(false)

	// PLAYING
	function click_trait() {
		// flip through view modes
		if (mode.value == view_modes.Neutral) {
			mode.value = view_modes.Viewing
		}
		else if (mode.value == view_modes.Viewing) {
			mode.value = view_modes.Small
		}
		else if (mode.value == view_modes.Small) {
			mode.value = view_modes.Viewing
			emit('show_trait', trait.value)
		}
	}

	function click_rating() {
		if(mode.value == view_modes.Editing) {
			edit_rating.value = true
		}
		else {
			play_trait()
		}
	}

	function play_trait() {
		/* add trait to dicepool */
		console.log("play_trait")
		if(
			// long pressing the trait enables viewing mode
			!held.value
			// dim all traits that don't have highlight when highlight is set
			// && !(props.highlight_root_id && !props.highlighted && !trait.value.requiredTraits?.map((t) => t.id).includes(props.highlight_root_id ?? ''))
		) {
			// when the player is in edit mode they can change the trait
			if (props.edit_mode && mode.value != view_modes.Editing) {
				switch_to_editing()
			}
			// otherwise add the trait to the dicepool
			else if(
				// traits without rating have no business here
				trait.value.rating
				// clicking the trait while editing shouldn't do anything
				&& mode.value != view_modes.Editing
				&& !player.editing
				// resources have a special function
				&& !['resource', 'empty'].includes(trait.value.ratingType ?? '')
				// only add dice when in the right phase
				&& inAddingPhase.value
			) {
				if(
					// the trait (or its subtraits) isn't already present in the dicepool
					trait.value.traitSettingId && !check_trait(trait.value.traitSettingId)
					// traitset trait limit isn't reached
					&& !traitset_limit_reached.value
					// traitset dice limit isn't reached
					// && traitset_dice(props.traitset_id ?? '').filter((d) => d.entityId == props.entity_id).length < (props.traitset_limit ?? 0)
				) {
					console.log("adding trait to dicepool")
					for(const die of trait.value.rating) {
						die.traitId = trait.value.id
						if(props.traitset_id) die.traitsetId = props.traitset_id
						if(props.entity_id) die.entityId = props.entity_id
						if(props.trait_setting_id) die.traitsettingId = props.trait_setting_id
						if(selected_sfx.value) die.sfxId = selected_sfx.value.id
						if(die.number_rating > 0) {
							add_die(_.clone(die))
						}
						else {
							if(
								// GMs can add challenges to function as complications against players
								(player.is_gm && trait.value.ratingType == 'challenge')
								// players can add other entities' complications to their own pool
								|| (
									player.the_entity
									&& props.entity_id != player.the_entity?.id
									&& props.entity_id != 'Entities/' + props.location_key
								)
							) {
								add_die(_.clone(die))
							}
							else {
								add_complication(_.clone(die))
							}
						}
					}
					// check if trait has any negative subtraits, they should be added as complications
					if(trait.value.subTraits && trait.value.subTraits.filter((st: Trait) => st.ratingType == 'static').length > 0) {
						for(const subtrait of trait.value.subTraits.filter((st: Trait) => st.ratingType == 'static')) {
							if(subtrait.rating && subtrait.rating.some((d) => d.number_rating < 0) && !check_trait(subtrait.traitSettingId ?? '')) {
								for(const die of subtrait.rating) {
									die.traitId = subtrait.id
									if(props.traitset_id) die.traitsetId = props.traitset_id
									if(props.entity_id) die.entityId = props.entity_id
									if(props.trait_setting_id) die.traitsettingId = props.trait_setting_id
									if(subtrait.traitSettingId) die.subTraitsettingId = subtrait.traitSettingId
									if(selected_sfx.value) die.sfxId = selected_sfx.value.id
									add_complication(_.clone(die))
								}
							}
						}
					}
					// if the trait has scaling, edit the dicepool limit
					if(trait.value.traitSetting?.scaling) {
						change_result_limit(trait.value.traitSetting.scaling, trait.value.traitSettingId ?? trait.value.traitSetting.id)
					}
					if(traitset_limit_reached.value) {
						emit('next_traitset')
					}
				}
				else if(check_trait(trait.value.traitSettingId ?? '')) {
					remove_traitsetting_dice(props.trait_setting_id ?? '')
					remove_complication_by_traitsetting(props.trait_setting_id ?? '')
					if(trait.value.subTraits && trait.value.subTraits?.length > 0) {
						for(const subtrait of trait.value.subTraits) {
							remove_traitsetting_dice(subtrait.traitSettingId ?? '')
							remove_complication_by_traitsetting(subtrait.traitSettingId ?? '')
						}
					}
					if(trait.value.traitSetting?.scaling) {
						change_result_limit(-1 * trait.value.traitSetting.scaling, trait.value.traitSettingId ?? trait.value.traitSetting.id)
					}
				}
			}
			// in case of resource and all rating die types are the same, decrease that by one
			else if(
				// traits without rating have no business here
				trait.value.rating
				// clicking the trait while editing shouldn't do anything
				&& mode.value != view_modes.Editing
				&& !player.editing
				// resources have a special function
				&& trait.value.ratingType == 'resource'
				// check if all rating die types are the same
				&& new Set(trait.value.rating.map((d) => d.rating)).size == 1
				// only add dice when in the right phase
				&& inAddingPhase.value
			) {
				deplete_resource(trait.value.rating[0])
			}
			// an exception to remove subtraits when the trait is empty
			else if(
				check_trait(trait.value.traitSettingId ?? '')
				&& trait.value.subTraits
				&& trait.value.subTraits?.length > 0
			) {
				for(const subtrait of trait.value.subTraits) {
					if(subtrait.rating && subtrait.rating.some((d) => d.number_rating > 0) && trait.value.traitSettingId) {
						remove_traitsetting_dice(trait.value.traitSettingId)
					}
					if(subtrait.rating && subtrait.rating.some((d) => d.number_rating < 0) && trait.value.traitSettingId) {
						remove_complication_by_traitsetting(trait.value.traitSettingId)
					}
				}
			}
		}
	}

	function click_subtrait(subtrait: Trait, cascade?: boolean) {
		/* add subtrait to dicepool */
		console.log("click_subtrait", traitset_limit_reached.value)
		if (!traitset_limit_reached.value // dicepool limit is not reached
			|| (player.editing && mode.value != view_modes.Editing)
		) {
			console.log("clicking subtrait, cascading to parent trait")
			play_trait()
		}
		
		// add subtrait to the dicepool
		if(
			!player.editing // clicking the trait while editing is handled by the subtrait component
			&& subtrait.traitSettingId
			&& !check_subtrait(subtrait.traitSettingId)
			&& inAddingPhase.value
		) {
			console.log("subtrait not in dicepool, adding")

			// add the subtrait
			if(subtrait.ratingType == 'static') {
				for(const die_type of subtrait.rating ?? []) {
					const { die } = useDie(die_type)
					die.value.traitId = trait.value.id
					if(props.traitset_id) die.value.traitsetId = props.traitset_id
					if(props.entity_id) die.value.entityId = props.entity_id
					if(props.trait_setting_id) die.value.traitsettingId = props.trait_setting_id
					if(subtrait.traitSettingId) die.value.subTraitsettingId = subtrait.traitSettingId
					if(
						// check traitset limit
						(
							!traitset_limit_reached.value
							|| check_trait(trait.value.traitSettingId ?? '')
						)
						&& die.value.number_rating > 0
					) {
						add_die(_.clone(die.value))
					}
					else if(die.value.number_rating < 0) {
						add_complication(_.clone(die.value))
					}
				}
			}
			else if(
				subtrait.ratingType == 'resource'
				&& subtrait.rating
				&& new Set(subtrait.rating.map((d) => d.number_rating)).size == 1
			) {
				// resource subtrait with all rating die types the same
				deplete_resource(subtrait.rating[0])
			}
			if(trait.value.traitSetting?.scaling) {
				console.log("changing result limit (scaling)")
				change_result_limit(
					trait.value.traitSetting.scaling,
					trait.value.traitSettingId ?? trait.value.traitSetting.id
				)
			}
			if(traitset_limit_reached.value) {
				emit('next_traitset')
			}
		}
		// remove the subtrait from the dicepool
		else if(!player.editing && subtrait.traitSettingId && check_subtrait(subtrait.traitSettingId)) {
			console.log("subtrait in dicepool, removing")
			if(subtrait.rating && subtrait.rating.some((d) => d.number_rating > 0)) {
				remove_traitsetting_dice(subtrait.traitSettingId)
			}
			if(subtrait.rating && subtrait.rating.some((d) => d.number_rating < 0)) {
				remove_complication_by_traitsetting(subtrait.traitSettingId)
			}
		}
		console.log("end click_subtrait")
	}

	function deplete_resource(dc: DieType) {
		console.log("depleting resource")
		if(
			mode.value != view_modes.Editing
			&& (
				trait.value.rating?.map((d) => d.id).includes(dc.id)
				|| new_rating.value.map((d) => d.id).includes(dc.id)
			)
			&& inAddingPhase.value
		) {
			if(new_rating.value.length > 0) {
				new_rating.value = new_rating.value.filter((d) => d.id != dc.id)
			}
			else {
				new_rating.value = trait.value.rating.filter((d) => d.id != dc.id)
			}
			mutate_trait_setting_temp({ 'rating': new_rating.value.map((r) => r.number_rating) })
			// const { die } = useDie({rating: dc})
			dc.traitId = trait.value.id
			if(props.traitset_id) dc.traitsetId = props.traitset_id
			if(props.entity_id) dc.entityId = props.entity_id
			if(props.trait_setting_id) dc.traitsettingId = props.trait_setting_id
			if(dc.number_rating > 0) {
				add_die(_.clone(dc))
				// change_result_limit(1)
			}
			else {
				add_complication(_.clone(dc))
			}
		}
		else if(mode.value == view_modes.Editing && !transfer_resource_mode.value) {
			edit_rating.value = true
		}
		else if(mode.value == view_modes.Editing && transfer_resource_mode.value && player.the_entity && props.entity_id != player.the_entity?.id) {
			// take resource from environment
			console.log("take resource from environment: " + JSON.stringify(dc))
			transfer_resource(player.the_entity.id, dc)
		}
		else if(mode.value == view_modes.Editing && transfer_resource_mode.value && player.the_entity && player.the_entity.location?.id && props.entity_id == player.the_entity?.id) {
			// put resource into envirnment
			transfer_resource(player.the_entity.location.id, dc)
		}
		setTimeout(() => {
			retrieve_trait()
		}, 200)
	}

	function deplete_challenge(d: DieType) {
		const index = new_rating.value.findIndex((r) => r.id == d.id)
		if(index >= 0) {
			const { die, change_type } = useDie(d)
			if(die.value.number_rating > 0) change_type(die.value.number_rating - 1)
			else change_type(die.value.number_rating + 1)
			if(die.value.number_rating != 0) {
				new_rating.value.splice(index, 1, die.value)
			}
			else {
				new_rating.value.splice(index, 1)
			}
		}
		mutate_trait_setting({ 'rating': new_rating.value.map((r) => r.number_rating ) })
	}

	const traitset_limit_reached = computed(() => {
		// trait traitset limit
		return [...new Set(traitset_dice(props.traitset_id ?? '').filter((d) => d.entityId == props.entity_id).map((d) => d.traitsettingId))].length >= (props.traitset_limit ?? 0)
		// dice traitset limit
		// return traitset_dice(props.traitset_id ?? '').filter((d) => d.entityId == props.entity_id).length < (props.traitset_limit ?? 1)
	})

	// EDITING
	// placeholders for mutating trait
	const new_ratingType: Ref<string> = ref(trait.value.ratingType ?? 'empty')
	const new_rating: Ref<DieType[]> = ref(trait.value.rating ?? [])
	const new_scaling: Ref<number> = ref(trait.value.traitSetting?.scaling ?? 0)
	const new_statement: Ref<string> = ref(trait.value.statement ?? "")
	const new_hidden: Ref<boolean> = ref(trait.value.traitSetting?.hidden ?? false)
	const new_notes: Ref<string> = ref(trait.value.notes ?? "")
	const new_sfxs: Ref<SFXType[]> = ref(trait.value.sfxs ?? [])
	const new_locationsEnabled: Ref<string[]> = ref(trait.value.traitSetting?.locationsEnabled ?? [])
	const new_locationsDisabled: Ref<string[]> = ref(trait.value.traitSetting?.locationsDisabled ?? [])
	const new_trait_id: Ref<string|undefined> = ref()

	function switch_to_editing() {
		reset_temporary_attributes()
		if(props.location_key) set_location_key(props.location_key)
		retrieve_location()
		retrieve_trait_setting('network-only')
		retrieve_possible_sfxs()
		if(
			trait.value.traitSetting?.locationsEnabled
			&& trait.value.traitSetting?.locationsEnabled?.length > 0
			&& location.value.parents
			// don't show the default restriction
			&& !trait.value.traitSetting.locationsEnabled.includes(location.value.parents[location.value.parents.length - 2].id)
		){
			restrict_location.value = true
		}
		else {
			restrict_location.value = false
		}
		editing_statement.value = trait.value.statement || trait.value.notes ? true : false
		editing_notes.value = trait.value.notes ? true : false
		edit_rating.value = false
		add_subtraits.value = false
		show_sfxs.value = false
		mode.value = view_modes.Editing
		if(
			player.is_gm
			|| props.entity_id == player.player_character.id
			|| props.entity_id?.startsWith('Relations/')
		) {
			can_edit.value = true
		}
	}

	const editing_trait_id = ref(false)

	function set_trait(_trait: Trait) {
		console.log("changing trait to: ", _trait)
		new_trait_id.value = _trait.id
	}

	const can_edit = ref<boolean>(false)

	function reset_temporary_attributes() {
		new_ratingType.value = trait.value?.ratingType ?? 'empty'
		new_rating.value = trait.value?.rating ?? []
		new_scaling.value = trait.value?.traitSetting?.scaling ?? 0
		new_statement.value = trait.value?.statement ?? ""
		new_notes.value = trait.value?.notes ?? ""
		new_sfxs.value = trait.value?.sfxs ?? []
		new_hidden.value = trait.value?.traitSetting?.hidden ?? false
		new_locationsEnabled.value = trait.value?.traitSetting?.locationsEnabled ?? []
		new_locationsDisabled.value = trait.value?.traitSetting?.locationsDisabled ?? []
	}

	watch(() => props.edit_mode, () => {
		if (props.edit_mode) {
			// switch_to_editing()
		}
		else {
			mode.value = view_modes.Neutral
		}
	})
	
	function longtap_trait(e: MouseEvent) {
		e.stopPropagation()
		held.value = true
		console.log("longtap")
		if(
			mode.value != view_modes.Editing
			// && (
			//	// disable trait editing for traits that aren't yours
			// 	player.is_gm
			// 	|| props.entity_id == player.player_character.id
			// 	|| props.entity_id.startsWith('Relations/')
			// )
		) {
			switch_to_editing()
		}
		setTimeout(() => held.value = false, 500)
	}

	const in_dicepool = computed(() => {
		if(trait.value.subTraits?.length == 0) {
			return check_trait(trait.value.traitSettingId ?? '')
		}
		return (
			check_trait(trait.value.traitSettingId ?? '')
			|| trait.value.subTraits?.some((st) => check_trait(st.traitSettingId ?? ''))
		)
	})

	// mutate trait when finished editing
	function change_trait(temp: boolean = false) {
		if(inherited.value) {
			overwrite_trait({
				'ratingType': new_ratingType.value,
				'rating': new_rating.value.map((r) => r.number_rating),
				'scaling': new_scaling.value,
				'statement': new_statement.value,
				'notes': new_notes.value,
				'sfxs': new_sfxs.value.map((sfx) => sfx.id),
				'locationsEnabled': new_locationsEnabled.value,
				'locationsDisabled': new_locationsDisabled.value,
				'inheritedAs': trait.value.traitSetting?.id ?? trait.value.traitSettingId ?? props.trait_setting_id,
				'hidden': new_hidden.value
			})
		}
		else if(temp === false) {
			console.log("changing trait")
			mutate_trait_setting({
				'newTraitId': new_trait_id.value,
				'ratingType': new_ratingType.value,
				'rating': new_rating.value.map((r) => r.number_rating),
				'scaling': new_scaling.value,
				'statement': new_statement.value,
				'notes': new_notes.value,
				'sfxs': new_sfxs.value.map((sfx) => sfx.id),
				'locationsEnabled': new_locationsEnabled.value,
				'locationsDisabled': new_locationsDisabled.value,
				'hidden': new_hidden.value
			})
		}
		else if(temp === true) {
			mutate_trait_setting_temp({
				'ratingType': new_ratingType.value,
				'rating': new_rating.value.map((r) => r.number_rating),
				'scaling': new_scaling.value,
				'statement': new_statement.value,
				'notes': new_notes.value,
				'sfxs': new_sfxs.value.map((sfx) => sfx.id),
				'locationsEnabled': new_locationsEnabled.value,
				'locationsDisabled': new_locationsDisabled.value,
				'hidden': new_hidden.value
			})
		}
	}

	function submit_changes(temp: boolean = false) {
		change_trait(temp)
		mode.value = view_modes.Neutral
		edit_rating.value = false
		show_sfxs.value = false
		// setTimeout(() => {
		// 	refetch(); retrieve_trait()
		// }, 200)
	}

	function cancel_edit() {
		retrieve_trait()
		mode.value = props.mode ?? view_modes.Small
		transfer_resource_mode.value = false
		edit_rating.value = false
		new_rating.value = []
		show_sfxs.value = false
	}


	const deletion = ref(false)
	async function delete_trait() {
		await unassign_trait()
		refetch()
	}

	function refetch() {
		setTimeout(() => emit('refetch'), 200)
	}

	const editing_statement = ref(trait.value.statement || trait.value.notes ? true : false)
	const editing_notes = ref(trait.value.notes ? true : false)
	
	const statement_examples = ref<string[]>([])
	const show_statement_examples = ref(false)
	async function display_statement_examples() {
		let temp = await retrieve_statement_examples()
		statement_examples.value = _.clone(temp).sort(() => 0.5 - Math.random())
		show_statement_examples.value = true
	}

	// render statement with first letter of each word bold
	const rendered_statement = computed(() => {
		if (!trait.value.statement) return ''
		const words = trait.value.statement.trim().split(/([\s\-\/])/)
		const parsed_words = words.map(word => {
			if (word.match(/^\d+$/)) return word
			return `<strong style="font-weight: 600; font-size: 0.8em; text-transform: uppercase">${word[0]}</strong>${word.slice(1)}`
		})
		const statement = parsed_words.join('').replace(/(\s)(\S)/g, (_, g1, g2) => `${g1}${g2}`).replace(/(\S)(\-|\s\/\s)(\S)/g, (_, g1, g2, g3) => `${g1}${g2}${g3}`)
		return marked.parse(statement)
	})

	const inherited = computed(() => {
		if(props.entity_id?.startsWith('Relations/')) {
			return trait.value.traitSetting?.fromEntity?.id != player.the_entity?.id
		}
		else if(props.trait_id != trait.value.id) {
			return true
		}
		else {
			return trait.value.traitSetting?.fromEntity?.id != props.entity_id
		}
	})


	// SFX stuff
	const { sfx_list, create_sfx, retrieve_sfx_list } = useSFXList()

	const edit_rating = ref(false)
	const edit_scaling = ref(false)
	const show_sfxs = ref(false)
	const selected_sfx = ref<SFXType>({} as SFXType)
	const expanded_sfx = ref<SFXType>({} as SFXType)
	const show_add_sfx = ref(false)
	const new_sfx_name = ref<string>('')
	const new_sfx_description = ref<string>('')

	function toggle_sfxs() {
		// retrieve_possible_sfxs()
		show_sfxs.value = !show_sfxs.value
	}

	function toggle_add_sfx() {
		show_add_sfx.value = !show_add_sfx.value
		if(show_add_sfx.value) retrieve_sfx_list()
	}

	function add_sfx(sfx: SFXType) {
		if(!trait.value.sfxs || trait.value.sfxs.length == 0) new_sfxs.value = [sfx]
		else new_sfxs.value = [...new_sfxs.value, sfx]
		change_trait()
		toggle_add_sfx()
	}

    function remove_sfx(sfx_id: string) {
		new_sfxs.value = new_sfxs.value.filter(sfx => sfx.id != sfx_id)
		expanded_sfx.value = {} as SFXType
    }

	function create_new_sfx() {
		create_sfx(new_sfx_name.value, new_sfx_description.value)
		setTimeout(() => {
			retrieve_sfx_list()
			watch(sfx_list, (newSfxList) => {
				console.log("new sfx list: ", newSfxList)
				const new_sfx = newSfxList.find(sfx => sfx.name == new_sfx_name.value)
				if(!new_sfx) return
				mutate_trait({
					possibleSfxs: [...(trait.value.possibleSfxs?.map((sfx) => sfx.id) ?? []), new_sfx.id]
				})
				new_sfx_name.value = ''
				new_sfx_description.value = ''
				show_add_sfx.value = false
				setTimeout(() => retrieve_possible_sfxs(), 200)
			}, { once: true })
		}, 200)
	}

	function change_rating(rating_type: string, rating: DieType[]) {
		new_ratingType.value = rating_type
		new_rating.value = rating
		// change_trait()
	}

	watch(() => player.editing, (newVal) => {
		if (!newVal) {
			mode.value = view_modes.Neutral;
		}
	})


	const add_subtraits = ref(false)
	async function add_subtrait(subtrait: Trait) {
		if(trait.value.traitSettingId && !trait.value.subTraits?.map((x) => x.id).includes(subtrait.id)) {
			await assign_subtrait(trait.value.traitSettingId, subtrait.id, props.entity_id)
		}
		// if(!inherited.value) {
		// 	retrieve_trait()
		// }
		// else {
		// 	refetch()
		// }
	}
	function remove_subtrait(subtrait: Trait) {
		if(subtrait.traitSettingId) {
			unassign_subtrait(subtrait.traitSettingId)
		}
		retrieve_trait()
	}

	// used for the location restriction widget
	function toggle_location_restriction(location_id: string) {
		if(location.value.parents) {
			const parent_location = location.value.parents[location.value.parents?.findIndex((l) => l.id == location_id) + 1]
			// clicking an enabled location removes it
			if(trait.value.traitSetting?.locationsEnabled?.includes(location_id)) {
				// mutate_trait({
				// 	'locationsEnabled': trait.value.traitSetting?.locationsEnabled?.filter((l) => l != location_id),
				// 	'locationsDisabled': trait.value.traitSetting?.locationsDisabled?.filter((l) => l != parent_location?.id) ?? []
				// })
				new_locationsEnabled.value = trait.value.traitSetting?.locationsEnabled?.filter((l) => l != location_id)
				new_locationsDisabled.value = trait.value.traitSetting?.locationsDisabled?.filter((l) => l != parent_location?.id) ?? []
			}
			// clicking elsewhere removes the current restriction and replaces it with the new one
			else {
				const new_enabled = trait.value.traitSetting?.locationsEnabled?.filter((l) => !location.value.parents?.map((l) => l.id).includes(l))
				const new_disabled = trait.value.traitSetting?.locationsDisabled?.filter((l) => !location.value.parents?.map((l) => l.id).includes(l))
				
				// mutate_trait({
				// 	'locationsEnabled': [...new Set([location_id, ...new_enabled ?? []])],
				// 	'locationsDisabled': [...new Set([parent_location?.id, ...new_disabled ?? []])]
				// })
				new_locationsEnabled.value = [...new Set([location_id, ...new_enabled ?? []])]
				new_locationsDisabled.value = [...new Set(['Entities/2', parent_location?.id, ...new_disabled ?? []])]
			}
			change_trait()
			setTimeout(() => {
				retrieve_trait()
			}, 200)
		}
	}

	const isLocationEnabled = (location_id?: string, index?: number): boolean => {
		return Boolean(
			(location_id && index)
			&& (
				trait.value.traitSetting?.locationsEnabled?.includes(location_id)
				|| isLocationEnabled(location.value.parents?.slice().reverse()[index - 1]?.id, index - 1)
			)
		) ?? false
	}

	const isLocationDisabled = (location_id?: string, index?: number): boolean => {
		return Boolean(
			(location_id && index)
			&& (
				trait.value.traitSetting?.locationsDisabled?.includes(location_id)
				|| isLocationDisabled(location.value.parents?.slice().reverse()[index - 1]?.id, index - 1)
			)
		) ?? true
	}

	// the location restriction index is to help navigate on mobile,
	// or when the user is in a deep level of the location hierarchy
	const location_restriction_index = ref(0)

	const restrict_location = ref(trait.value.traitSetting?.locationsDisabled ? true : false)
	watch(restrict_location, (newVal) => {
		if(!location.value.parents) {
			retrieve_parents()
		}
	})

	async function steal() {
		if(trait.value.ratingType == 'resource' && new Set(trait.value.rating?.map(d => d.number_rating)).size > 1) {
			transfer_resource_mode.value = !transfer_resource_mode.value
		}
		else if(player.the_entity && props.entity_id != player.the_entity?.id) {
			await change_trait_entity(player.the_entity.id)
			emit('refetch')
		}
		else if(player.the_entity && player.the_entity?.location && props.entity_id == player.the_entity?.id) {
			await change_trait_entity(player.the_entity.location?.id)
			emit('refetch')
		}
	}

	const transfer_resource_mode = ref(false)

	function copy() {
		copy_trait({
			'ratingType': new_ratingType.value,
			'rating': new_rating.value.map((r) => r.number_rating),
			'scaling': new_scaling.value,
			'statement': new_statement.value,
			'notes': new_notes.value,
			'sfxs': new_sfxs.value.map((sfx) => sfx.id),
			'locationsEnabled': new_locationsEnabled.value,
			'locationsDisabled': new_locationsDisabled.value
		})
		refetch()
	}

	const show_pc_visible = ref(false)
	const showable_characters = computed(() => {
		// show local characters that can gain this insight
		return location.value.entities?.filter((e) => 
			e.entityType == 'character'
			// && e.active
			&& e.id != props.entity_id
		) ?? []
	})
	watch(location, (newLocation) => {
		// if the trait has location restrictions,
		// make sure the breadcrumbs show the relevant restriction
		if(
			trait.value.traitSetting?.locationsEnabled
			&& trait.value.traitSetting?.locationsEnabled?.length > 0
		) {
			const first_location_index = location.value.parents?.map((l) => l.id)
						.indexOf(trait.value.traitSetting?.locationsEnabled[0]) ?? 0
			if(first_location_index >= 1) {
				location_restriction_index.value = first_location_index - 1
			}
			else {
				location_restriction_index.value = first_location_index
			}
		}

		
	})
	function show_pcs() {
		console.log("show_pc_show")
		// if(showable_characters.value.length == 1) {
		// 	toggle_known(showable_characters.value[0].id)
		// }
		show_pc_visible.value = true
	}
	function toggle_show_pc_visible() {
		show_pc_visible.value = !show_pc_visible.value
	}
	function toggle_known(character_id: string) {
		// if(trait.value.traitSetting?.knownTo) {
			if(!(trait.value.traitSetting?.knownTo ?? []).map((e) => e.id).includes(character_id)) {
				mutate_trait_setting({ 'knownTo': [
					...trait.value.traitSetting?.knownTo?.map((e) => e.id).filter((e) => e != character_id) ?? [],
					character_id
				] })
			}
			else {
				mutate_trait_setting({ 'knownTo': trait.value.traitSetting?.knownTo?.map((e) => e.id).filter((e) => e != character_id) ?? [] })
			}
		// }
		setTimeout(() => {
			retrieve_trait()
			retrieve_presence()
		}, 200)
	}
	function toggle_hidden() {
		mutate_trait_setting({ 'hidden': new_hidden.value })
	}

	const passes_filter = computed(() => {
		if(!props.filter) {
			return true
		}
		else if(
			props.filter &&
			(
				trait.value.name.toLowerCase().includes(props.filter.toLowerCase()) ||
				trait.value.statement?.toLowerCase().includes(props.filter.toLowerCase()) ||
				trait.value.notes?.toLowerCase().includes(props.filter.toLowerCase())
			)
		) {
			// if the filter string is contained in the name or statement of the trait
			return true
		}
		else {
			return false
		}
	})

	const styling_rating = computed(() => {
		if(new_rating.value.length > 0) {
			const max_rating = Math.max(...new_rating.value.map((r) => Math.abs(r.number_rating)))
			const sign = Math.max(...new_rating.value.map((r) => r.number_rating)) > 0 ? 'positive' : 'negative'
			return { rating: die_constants.find(d => d.number_rating == max_rating)?.rating, sign: sign }
		}
		else if(trait.value.rating && trait.value.rating.length > 0) {
			const max_rating = Math.max(...trait.value.rating.map((r) => Math.abs(r.number_rating)))
			const sign = Math.max(...trait.value.rating.map((r) => r.number_rating)) > 0 ? 'positive' : 'negative'
			return { rating: die_constants.find(d => d.number_rating == max_rating)?.rating, sign: sign }
		}
	})

	watch(() => player.session_id, (newSessionId, oldSessionId) => {
		if(newSessionId != oldSessionId) {
			retrieve_trait()
		}
	})

	const trait_explanation = computed(() => {
		if(trait.value.explanation && mode.value == view_modes.Small && trait.value.explanation.length > 50) {
			return trait.value.explanation.substring(0, 50) + '...'
		}
		else {
			return trait.value.explanation
		}
	})
</script>

<template>
	<div class="trait"
			:class="[
				mode,
				in_dicepool ? 'active' : 'inactive',
				trait.ratingType ?? '',
				trait.statement ? 'with-statement' : 'without-statement',
				// trait.ratingType != 'empty' && trait.rating && trait.rating.length > 0 && trait.rating[0].rating && trait.ratingType != 'empty' ? trait.rating[0].rating : 'empty',
				styling_rating?.rating?.length ?? 0 > 0 ? styling_rating?.rating : 'empty',
				// trait.ratingType != 'empty' && trait.rating && trait.rating.length > 0 && trait.rating[0].number_rating > 0 ? 'positive' : 'negative',
				styling_rating?.sign,
				trait.sfxs && trait.sfxs?.length > 0 ? 'with-sfxs' : 'without-sfxs',
				trait.subTraits && trait.subTraits?.length > 0 ? 'with-subtraits' : 'without-subtraits',
				props.highlighted || trait.requiredTraits?.map((t) => t.id).includes(props.highlight_root_id ?? '') ? 'highlighted' : '',
				// dim all traits that don't have highlight when highlight is set
				props.highlight_root_id && !props.highlighted && !trait.requiredTraits?.map((t) => t.id).includes(props.highlight_root_id ?? '') ? 'dim' : '',
				{ 'clickable': mode != view_modes.Editing },
				{ 'inherited': inherited },
				{ 'hidden': (trait.traitSetting?.hidden ?? false) && player.is_gm && mode == view_modes.Small },
			]"
			v-if="trait && passes_filter"
			v-touch:hold="longtap_trait"
			@click.right="longtap_trait"
			@click="click_trait"
			@contextmenu="(e) => e.preventDefault()">
		
		<div class="trait-inner">


			<div class="edit-setting-buttons" :class="{ 'small-buttons': player.small_buttons }" v-if="mode == view_modes.Editing">
				<div class="button-mnml copy-id-button"
						title="copy traitsetting id"
						@click="copy_id"
						v-if="player.is_gm">
					<div class="icon">#</div>
					<div class="label" v-if="!player.small_buttons">copy ID</div>
				</div>
				<div class="button-mnml trait-id-button"
						:class="editing_trait_id ? 'active' : 'inactive'"
						v-if="can_edit"
						@click="editing_trait_id = !editing_trait_id">
					<div class="icon">&#x2015;</div>
					<div class="label" v-if="!player.small_buttons">{{ editing_trait_id ? 'cancel' : 'trait' }}</div>
				</div>
				<div class="button-mnml statement-button"
						:class="editing_statement ? 'active' : 'inactive'"
						v-if="!trait.statement && can_edit"
						@click="() => {
							editing_statement = !editing_statement;
							new_statement = trait.statement ?? '';
						}">
					<div class="icon">📄</div>
					<div class="label" v-if="!player.small_buttons">{{ editing_statement ? 'cancel' : 'statement' }}</div>
				</div>
				<div class="button-mnml notes-button"
						:class="editing_notes ? 'active' : 'inactive'"
						v-if="!trait.notes && can_edit"
						@click="() => {
							editing_notes = !editing_notes;
							new_notes = trait.notes ?? '';
						}">
					<div class="icon">📄</div>
					<div class="label" v-if="!player.small_buttons">{{ editing_notes ? 'cancel' : 'notes' }}</div>
				</div>
				<div class="button-mnml rating-button"
						:class="edit_rating ? 'active' : 'inactive'"
						@click="edit_rating = !edit_rating"
						v-if="can_edit">
					<div class="icon">🎲</div>
					<div class="label" v-if="!player.small_buttons">{{ edit_rating ? 'cancel' : 'rating' }}</div>
				</div>
				<!-- <div class="button-mnml scaling-button"
						:class="edit_scaling ? 'active' : 'inactive'"
						@click="edit_scaling = !edit_scaling"
						v-if="can_edit">
					<div class="icon">📈</div>
					<div class="label" v-if="!player.small_buttons">{{ edit_scaling ? 'cancel' : 'scaling' }}</div>
				</div> -->
				<ButtonMinimal :function="ButtonTypes.SCALING"
					:class="{'active': edit_scaling}"
					@click="edit_scaling = !edit_scaling" />
				<div class="button-mnml subtrait-icon"
						:class="add_subtraits ? 'active' : 'inactive'"
						v-if="trait.possibleSubTraits
							&& trait.possibleSubTraits?.filter((x) => !trait.subTraits?.map((y) => y.id).includes(x.id)).length > 0
							&& can_edit"
						@click="add_subtraits = !add_subtraits">
					<div class="icon">⪽</div>
					<div class="label" v-if="!player.small_buttons">{{ add_subtraits ? 'cancel' : 'add subtrait' }}</div>
				</div>
				<div class="button-mnml sfx-button"
						:class="show_sfxs ? 'active' : 'inactive'"
						@click="toggle_sfxs"
						v-if="(trait.possibleSfxs?.length ?? 0) > 0 && can_edit">
					<div class="icon">✨</div>
					<div class="label" v-if="!player.small_buttons">{{ show_sfxs ? 'cancel' : 'add sfx' }}</div>
				</div>
				<div class="button-mnml copy-button"
						@click.stop="copy">
					<div class="icon">⧉</div>
					<div class="label" v-if="!player.small_buttons">duplicate trait</div>
				</div>
				<div class="button-mnml transfer-resource-button"
						:class="transfer_resource_mode ? 'active' : 'inactive'"
						:title="'take ' + trait.name"
						@click.stop="steal"
					v-if="props.entity_id != player.the_entity?.id && !inherited">
					<div class="icon">🫳</div>
					<div class="label" v-if="!player.small_buttons">take {{ trait.name }}</div>
				</div>
				<div class="button-mnml transfer-resource-button"
						:class="transfer_resource_mode ? 'active' : 'inactive'"
						:title="'drop ' + trait.name"
						@click.stop="steal"
						v-if="props.entity_id == player.the_entity?.id && !inherited && props.traitset_types?.includes('location')">
					<div class="icon">🫳</div>
					<div class="label" v-if="!player.small_buttons">drop {{ trait.name }}</div>
				</div>
				<div class="button-mnml visible-button"
						:class="show_pc_visible ? 'active' : 'inactive'"
						@click.stop="show_pc_visible ? show_pc_visible = false : show_pcs()"
						@click.right="toggle_show_pc_visible"
						v-touch:hold="toggle_show_pc_visible"
						@contextmenu="(e) => e.preventDefault()"
						v-if="player.is_gm && can_edit">
					<div class="icon">🧠</div>
					<div class="label" v-if="!player.small_buttons">show PC</div>
				</div>
				<ButtonMinimal :function="ButtonTypes.LOCATION_PIN"
					v-if="can_edit && !props.entity_id?.startsWith('Relations/')"
					@click.stop="restrict_location = !restrict_location" />
				<div class="button-mnml restrict-location-button"
						:class="restrict_location ? 'active' : 'inactive'"
						@click="restrict_location = !restrict_location"
						v-if="can_edit && !props.entity_id?.startsWith('Relations/')">
					<div class="icon">🗺</div>
					<div class="label" v-if="!player.small_buttons">{{ restrict_location ? 'cancel' : 'restrict by location' }}</div>
				</div>
			</div>
				
			<div class="descriptor" :class="[trait.statement ? 'with-statement' : 'without-statement',
						trait.sfxs && trait.sfxs?.length > 0 ? 'with-sfxs' : 'without-sfxs',]">
				<div class="trait-image" v-if="trait.traitSetting?.toEntity && !props.entity_id?.startsWith('Relations/')">
					<EntityButton :entity_id="trait.traitSetting.toEntity.id" :show_icon="false" :show_name="false" class="trait-to-entity" is_active />
				</div>
				<div class="trait-text">
					<div class="label trait-name" @click="mode == view_modes.Editing ? editing_trait_id = !editing_trait_id : null">
						<span class="name">
							<span class="trait-inherited" v-if="inherited && player.is_gm">· </span>
							<span class="trait-name-label">
								{{ trait.name }}
							</span>
							<span class="label trait-owner" v-if="(mode == view_modes.Editing
										|| player.is_gm
									)
									&& trait.traitSetting?.fromEntity?.name">
								{{ ' from ' + trait.traitSetting?.fromEntity?.name }}
							</span>
							<span class="label trait-owner-self" v-if="mode == view_modes.Editing
									&& trait.traitSetting?.fromEntity?.id == player.the_entity?.id">
								{{ ' (self)' }}
							</span>
						</span>
						<span class="rating-type label" v-if="preferredColor == 'light' || mode == view_modes.Viewing">
							{{ trait.ratingType ?? 'empty' }}
						</span>
						<span class="scaling label" v-if="trait.traitSetting?.scaling">
							{{ trait.traitSetting?.scaling > 0 ? '+' :
								trait.traitSetting?.scaling < 0 ? '-' : '' }}
							{{ trait.traitSetting?.scaling ?? '' }}
						</span>
					</div>
					<div class="statement" v-if="trait.statement && mode != view_modes.Editing"
						v-html="rendered_statement" />

					<div class="edit-statement edit-attribute" v-if="editing_statement && mode == view_modes.Editing">
						<div class="edit-statement-1">
							<input type="text" name="text-statement" ref="text-statement"
								class="statement statement-edit"
								:class="{ 'changed': new_statement != (trait.statement ?? '') }"
								v-model="new_statement"
								placeholder="statement"
								@input="!show_statement_examples ? display_statement_examples() : undefined"
								@contextmenu="(e) => e.stopPropagation()" />
							<span class="statement-length" :class="{ 'exceeded': new_statement && new_statement.split(/\s+/).length > 7}">
								{{ new_statement ? new_statement.split(/\s+/).length + '/7' : '' }}
							</span>
							<div class="statement-examples">
								<input type="button" class="button-mnml statement-example"
									:value="example"
									v-for="example in statement_examples.filter((x) => x.toLowerCase().includes(new_statement.toLocaleLowerCase())).slice(0, 3)"
									@click.stop="new_statement = example">
								<input type="button" class="button"
									:value="player.small_buttons ? '💡' : '💡' + (new_statement ? ' auto-complete' : ' examples')"
									v-if="!new_statement || statement_examples.filter((x) => x.toLowerCase().includes(new_statement.toLocaleLowerCase())).length > 0"
									@click="display_statement_examples" />
							</div>
						</div>
					</div>
					<div class="required-traits label" v-if="mode == view_modes.Viewing || player.viewing">
						<div v-if="trait.requiredTraits && trait.requiredTraits?.length > 0">
							required traits:
							<ul>
								<li v-for="require_traits in trait.requiredTraits">
									<div>{{ require_traits.name }}</div>
								</li>
							</ul>
						</div>
					</div>
				</div>


				<div class="rating" :class="{ 'take-resource': transfer_resource_mode }"
						v-if="trait.ratingType != 'empty'"
						@click.stop="(mode == view_modes.Editing && !transfer_resource_mode && can_edit) ? edit_rating = true : undefined">
					<Rating v-if="trait.rating"
						:rating="new_rating.length > 0 ? new_rating : trait.rating"
						:rating-type="trait.ratingType"
						@click.stop="click_rating"
						@deplete-resource="deplete_resource"
						@deplete-challenge="(d) => mode == view_modes.Editing ? edit_rating = true : deplete_challenge(d)" />
				</div>
			</div>

			<div class="notes" v-html="marked.parse(trait.notes)"
				v-if="trait.notes
				&& mode != view_modes.Editing
				&& (
					mode != view_modes.Small ||
					!trait.statement
				)
				&& (player.is_gm
					|| props.entity_id == player.player_character.id
					|| props.entity_id?.startsWith('Relations/')
				)" />
			
			<div class="edit-trait" v-if="mode == view_modes.Editing">
				<div class="edit-trait-id" v-if="mode == view_modes.Editing && editing_trait_id">
					<div class="edit-trait-label">
						change trait
					</div>
					<TraitSelector class="edit-trait-selector"
						:traitset_id="trait.traitsetId"
						:entity_type="props.entity_type"
						:entity="props.entity"
						@set_trait="(_trait) => set_trait(_trait)" />
				</div>

				<div class="edit-notes edit-attribute" v-if="editing_notes">
					<textarea class="notes" :class="{ 'changed': (trait.notes ?? '') != new_notes }" v-model="new_notes" placeholder="notes" @contextmenu="(e) => e.stopPropagation()"
						v-if="player.is_gm || (props.entity_id == player.player_character.id || props.entity_id?.startsWith('Relations/'))" />
				</div>

				<div class="edit-rating edit-attribute" v-if="edit_rating">
					<RatingEdit
						v-if="trait.ratingType && trait.rating"
						:rating_type="new_ratingType"
						:rating="new_rating"
						@change-rating="(rating_type: string, rating: DieType[]) => change_rating(rating_type, rating)"
						@cancel="edit_rating = false" />
				</div>

				<div class="edit-scaling edit-attribute" v-if="edit_scaling">
					<input type="button" class="button" value="-" @click="new_scaling = (new_scaling - 1) < 0 ? 0 : new_scaling - 1" />
					<span>{{ new_scaling }}</span>
					<input type="button" class="button" value="+" @click="new_scaling = new_scaling + 1" />
				</div>

				<div class="add-sub-traits edit-attribute"
						v-if="trait.possibleSubTraits
							&& trait.possibleSubTraits?.filter((x) => !trait.subTraits?.map((y) => y.id).includes(x.id)).length > 0
							&& mode == view_modes.Editing
							&& add_subtraits">
					<span>add sub-trait:</span>
					<input type="button" class="button"
						v-for="subtrait in trait.possibleSubTraits.filter((x) => !trait.subTraits?.map((y) => y.id).includes(x.id)
							&& (x.traitset?.entityTypes?.includes('subtrait') || x.traitSettingId))"
						:value="subtrait.name"
						@click="add_subtrait(subtrait)" />
				</div>

				<div class="show-character" v-if="show_pc_visible">
					<input type="checkbox" id="hidden" name="hidden" v-model="new_hidden" @change="toggle_hidden" />
					<label for="hidden">hidden by default</label>
					<div class="show-character-list" v-if="new_hidden">
						<div class="character-list">
							<span class="show-character-title">known to:</span>
							<span v-if="!trait.traitSetting?.knownTo?.length">
								<i>no one</i>
							</span>
							<EntityButton
								v-for="entity_id in trait.traitSetting?.knownTo?.map((x) => x.id)" :key="entity_id"
								:entity_id="entity_id"
								:override_click="true"
								is_active
								@click_entity="toggle_known(entity_id)" />
						</div>
						<div class="character-list">
							<span class="show-character-title">hidden from:</span>
							<span v-if="!showable_characters.filter((x: EntityType) => !trait.traitSetting?.knownTo?.map((y: EntityType) => y.id).includes(x.id)).length">
								<i>no one</i>
							</span>
							<EntityButton
								v-for="entity in showable_characters.filter((x: EntityType) => !trait.traitSetting?.knownTo?.map((y: EntityType) => y.id).includes(x.id))" :key="entity.id"
								:entity_id="entity.id"
								:override_click="true"
								:is_active="false"
								@click_entity="toggle_known(entity.id)" />
						</div>
					</div>
				</div>

				<div class="location-restrictions edit-attribute">
					<div class="location-restriction-container" v-if="restrict_location">
						<a class="location-restriction"
								v-for="(location, index) in location.parents?.slice().reverse()"
								:key="location.key"
								@click.stop="toggle_location_restriction(location.id)"
								:class="{
									'enabled': isLocationEnabled(location.id, index),
									'explicitly-enabled': trait.traitSetting?.locationsEnabled?.includes(location.id),
									'disabled': isLocationDisabled(location.id, index),
									'explicitly-disabled': trait.traitSetting?.locationsDisabled?.includes(location.id)
								}">
							{{ location.name }}
						</a>
					</div>
				</div>
			</div>

			<div class="label explanation"
				title="trait explanation"
				v-if="trait.explanation &&
					(
						preferredColor == 'light' ||
						[view_modes.Viewing, view_modes.Editing].includes(mode) ||
						// mode == view_modes.Viewing ||
						// mode == view_modes.Editing ||
						player.viewing
					)"
				v-html="marked(trait_explanation ?? '')">
			</div>

			<div class="sfxs" v-if="(trait.sfxs && trait.sfxs?.length > 0) || show_sfxs">
				<!-- <div v-if="(trait.sfxs && trait.sfxs?.length > 0 && !expanded_sfx.id)" class="sfx-sparkles section-icon">✨</div> -->
				<div class="sfx-list">
					<template v-for="(sfx, i) in (mode == view_modes.Editing ? new_sfxs : trait.sfxs)" :key="sfx.id">
						<SFX :sfx_id="sfx.id" :trait-setting-id="trait.traitSettingId"
							@expand="expanded_sfx = sfx"
							@collapse="expanded_sfx = {} as SFXType"
							@activate="selected_sfx = sfx; click_trait()"
							@remove="remove_sfx(sfx.id)"
							:editing="mode == view_modes.Editing"
							:adding="false"
							:expanded="mode != view_modes.Small || expanded_sfx.id == sfx.id" />
							<!-- v-if="expanded_sfx.id ? sfx.id == expanded_sfx.id : true" /> -->
						<!-- <span class="sfx-divider" v-if="(i < (trait.sfxs?.length ?? 0) - 1) && !expanded_sfx.id">/</span> -->
					</template>
				</div>
				<div class="add-sfx" v-if="mode == view_modes.Editing && trait.possibleSfxs">
					<div class="add-sfx-list">
						<template v-for="(sfx, i) in trait.possibleSfxs.filter((sfx) => !new_sfxs.map((x) => x.id).includes(sfx.id))" :key="sfx.id">
							<SFX :sfx_id="sfx.id" :trait-setting-id="trait.traitSettingId"
								:editing="mode == view_modes.Editing" @add="add_sfx(sfx)" adding />
							<!-- <span class="sfx-divider" v-if="i < (sfx_list?.length ?? 0) - 1">/</span> -->
						</template>
						<input type="button" class="button add-sfx-title"
							@click.stop="toggle_add_sfx" :value="show_add_sfx ? 'X' : '+'" />
					</div>
					<div class="create-sfx" v-if="show_add_sfx">
						<input type="text" class="add-sfx-name" placeholder="name" v-model="new_sfx_name" />
						<textarea type="text" class="add-sfx-description" placeholder="description" v-model="new_sfx_description" />
						<input type="button" class="button" value="create"
							@click="create_new_sfx"
							v-if="new_sfx_name && new_sfx_description" />
					</div>
				</div>
			</div>

			<div class="sub-traits" v-if="trait.subTraits && trait.subTraits?.length > 0">
				<div class="section-icon">⪽</div>
				<div>
					<div class="sub-traits-list positive">
						<template v-for="subtrait in trait.subTraits.filter((x) => x.rating?.reduce((a, b) => a + b.number_rating, 0) > 0)" :key="subtrait.traitSettingId">
							<SubTrait v-if="subtrait.traitSettingId"
								:trait_setting_id="subtrait.traitSettingId"
								:editing_trait="mode == view_modes.Editing"
								:edit_mode="props.edit_mode"
								:entity_id="props.entity_id"
								:parent_traitset_id="trait.traitsetId ?? trait.traitset?.id"
								:parent_traitsetting_id="trait.traitSetting?.id ?? trait.traitSettingId"
								@click_subtrait="click_subtrait(subtrait, true)"
								@next_traitset="emit('next_traitset')"
								@remove_subtrait="remove_subtrait(subtrait)" />
						</template>
					</div>
				</div>
				<div>
					<div class="sub-traits-list neutral">
						<template v-for="subtrait in trait.subTraits.filter((x) => x.rating?.reduce((a, b) => a + b.number_rating, 0) == 0)" :key="subtrait.traitSettingId">
							<SubTrait v-if="subtrait.traitSettingId"
								:trait_setting_id="subtrait.traitSettingId"
								:editing_trait="mode == view_modes.Editing"
								:edit_mode="props.edit_mode"
								:entity_id="props.entity_id"
								:parent_traitset_id="trait.traitsetId ?? trait.traitset?.id"
								@click_subtrait="click_subtrait(subtrait)"
								@remove_subtrait="remove_subtrait(subtrait)" />
						</template>
					</div>
				</div>
				<div>
					<div class="sub-traits-list negative">
						<template v-for="subtrait in trait.subTraits.filter((x) => x.rating?.reduce((a, b) => a + b.number_rating, 0) < 0)" :key="subtrait.traitSettingId">
							<SubTrait v-if="subtrait.traitSettingId"
								:trait_setting_id="subtrait.traitSettingId"
								:editing_trait="mode == view_modes.Editing"
								:edit_mode="props.edit_mode"
								:entity_id="props.entity_id"
								:parent_traitset_id="trait.traitsetId ?? trait.traitset?.id"
								@click_subtrait="click_subtrait(subtrait)"
								@remove_subtrait="remove_subtrait(subtrait)" />
						</template>
					</div>
				</div>
			</div>

			<div class="edit-buttons" :class="{ 'small-buttons': player.small_buttons }"
					v-if="mode == view_modes.Viewing ||
						mode == view_modes.Editing">
				<div type="button" class="button-mnml play-button"
						@click.stop="play_trait"
						v-if="mode == view_modes.Viewing">
					<div class="icon">▶</div>
					<div class="label" v-if="!player.small_buttons">play trait</div>
					<!-- {{ player.small_buttons ? '▶' : '▶ play trait' }} -->
				</div>
				
				<div type="button" class="button-mnml edit-button"
						@click.stop="switch_to_editing"
						v-if="mode == view_modes.Viewing">
					<div class="icon">✎</div>
					<div class="label" v-if="!player.small_buttons">edit trait</div>
					<!-- {{ player.small_buttons ? '✎' : '✎ edit trait' }} -->
				</div>
				
				<div  type="button" class="button-mnml save-button"
						@click.stop="submit_changes(false)"
						v-if="can_edit && mode == view_modes.Editing">
					<div class="icon">🖪</div>
					<div class="label" v-if="!player.small_buttons">perma-{{ (inherited ? 'overwrite' : 'save') }}</div>
					<!-- {{ player.small_buttons ? '🖪' : '🖪' + (inherited ? 'overwrite' : 'save') + ' trait' }} -->
				</div>
				
				<div type="button" class="button-mnml save-temp-button"
						@click.stop="submit_changes(true)"
						v-if="can_edit && mode == view_modes.Editing">
					<div class="icon">🖫</div>
					<div class="label" v-if="!player.small_buttons">session {{ (inherited ? 'overwrite' : 'save') }}</div>
					<!-- {{ player.small_buttons ? '🖫' : '🖫' + (inherited ? 'overwrite' : 'save') + ' trait\n(this session only)' }} -->
				</div>

				<div type="button" class="button-mnml cancel-button"
						@click.stop="cancel_edit"
						v-if="[view_modes.Editing, view_modes.Viewing].includes(mode)">
					<div class="icon">✖</div>
					<div class="label" v-if="!player.small_buttons">close</div>
					<!-- {{ player.small_buttons ? '✖' : '✖ cancel' }} -->
				</div>
				<ButtonMinimal :function="ButtonTypes.TRASH" label="perma-delete"
					class="remove-button"
					@click.stop="deletion = true"
					v-if="can_edit && !inherited && mode == view_modes.Editing && !deletion" />
				<div id="delete-confirmation" v-if="deletion">
					<ButtonMinimal :function="ButtonTypes.TRASH" label="confirm" />
					<!-- <div class="button-mnml confirm" id="confirm-delete"
							title="confirm deletion">
						<div class="icon">🗑</div>
						<div class="label">confirm</div>
					</div> -->
					<div class="button-mnml verify" id="verify-delete"
							title="confirm and delete"
							@click="delete_trait">
						<div class="icon">✔</div>
						<div class="label">yes</div>
					</div>
					<div class="button-mnml cancel" id="cancel-delete"
							title="cancel deletion"
							@click="deletion = false">
						<div class="icon">✗</div>
						<div class="label">cancel</div>
					</div>
				</div>

			</div>
		</div>
	</div>
</template>

<style scoped>
	.trait {
		text-align: left;
		display: flex;
		flex-direction: column;
		max-height: 100%;
		/* overflow-y: auto; */
		.traitset-name {
			font-size: small;
		}
		.descriptor {
			display: flex;
			.trait-to-entity {
				width: 5em;
			}
			.trait-text .trait-name {
				display: flex;
				justify-content: space-between;
				.label {
					font-size: 9pt;
				}
			}
		}
		.descriptor.without-statement.without-sfxs {
			vertical-align: top;
		}
		.descriptor.without-statement.with-sfxs {
			vertical-align: super;
		}
		.trait-text {
			flex-grow: 2;
		}
		.copy-id, .edit {
			float: right;
			margin: 0;
		}
		.scaling {
			font-size: 2em !important;
			transform: translateY(+.4em);
			white-space: nowrap;
		}
		.statement {
			padding-left: .5em;
			width: 100%;
			/* max-height: 5em; */
			overflow: hidden;
			strong {
				font-weight: 100;
				background-color: red;
			}
		}
		.rating {
			text-align: right;
			padding: 0 .5em;
			max-height: 100%;
		}
		.sfxs {
			font-size: .8em;
			position: relative;
			padding-left: 1.5em;
			.sfx-sparkles {
				position: absolute;
				left: 0;
				top: 2px;
			}
			.sfx-list {
				/* display: flex; */
			}
			.sfx-divider {
				margin: 0 .5em;
			}
		}
		.edit-trait {
			padding: 0 1em;
			/* .edit-rating {
				display: flex;
				align-items: start;
			} */
		}
		.sub-traits {
			display: flex;
			flex-direction: column;
			gap: .2em;
			padding: .4em 1em .4em 2em;
			position: relative;
			.section-icon {
				position: absolute;
				left: 10px;
				top: 15px;
				font-size: 1.6em;
				line-height: 0;
				color: var(--color-highlight);
			}
			.sub-traits-list {
				display: flex;
				justify-content: end;
				gap: .4em 1em;
				flex-wrap: wrap;
			}
		}
		&.highlighted .trait-inner {
			border: 1px solid var(--color-highlight);
			color: var(--color-highlight-text);
			background-image: linear-gradient(45deg, var(--color-highlight) -20%,
								var(--color-background) 120%) !important;
		}
		.edit-setting-buttons {
			display: flex;
			/* flex-wrap: wrap; */
			min-height: 4em;
			overflow-x: auto;
			gap: 1px;
			background-color: var(--color-border);
			border-color: var(--color-border-hover);
			/* overflow: hidden; */
			/* position: sticky; */
			/* top: 0; */
			/* z-index: 5; */
			.button-mnml {
				flex-grow: 1;
				padding: 1em .4em;
				background-color: var(--color-background);
				&.active {
					background-color: var(--color-editing);
					color: var(--color-editing-text);
				}
				&:hover {
					background-color: var(--color-highlight);
					color: var(--color-highlight-text);
				}
			}
			&.small-buttons .button-mnml {
				font-size: 1.2em;
				&.subtrait-icon.inactive {
					font-size: 2em;
					line-height: 0;
				}
			}
		}
		.edit-buttons {
			display: flex;
			min-height: 3em;
			position: sticky;
			bottom: 0;
			z-index: 1;
			.button-mnml {
				flex-grow: 1;
				margin: 0;
				padding: .5em 0;
			}
			&.small-buttons .button-mnml {
				font-size: 1.2em;
			}
			.button-mnml:hover {
				font-weight: bold;
				flex-grow: 1.5;
			}
			.play-button {
				background-color: var(--color-highlight);
				color: var(--color-highlight-text);
			}
			.edit-button {
				background-color: var(--color-editing);
				color: var(--color-editing-text);
			}
			.save-button {
				border-right: 1px solid var(--color-editing);
				background-color: var(--color-highlight);
				color: var(--color-highlight-text);
			}
			.save-temp-button {
				background-color: var(--color-editing);
				color: var(--color-editing-text);
			}
			.cancel-button {
				background-color: var(--color-background);
				color: var(--color-text);
			}
			.remove-button {
				border-left: 1px solid var(--color-editing);
				background-color: var(--color-hitch);
				color: var(--color-hitch-text);
			}
			#delete-confirmation {
				display: flex;
				flex-grow: 1;
				border: 3px solid var(--color-hitch);
				align-items: center;
				label {
					font-size: 1.2em;
					padding: 0 1em;
				}
				.button-mnml {
					height: 100%;
					&.verify {
						background-color: var(--color-hitch);
						color: var(--color-hitch-text);
					}
				}
			}
		}
		&.editing {
			border-color: var(--color-highlight);
			width: 100%;
			display: flex;
			flex-direction: column;
			gap: 1em;
			.location-restriction-container {
				/* https://codepen.io/dp_lewis/pen/MWYgbOY */
				border-radius: 25px;
				border: 1px solid var(--color-border);
				display: inline-flex;
				overflow: hidden;
				flex-wrap: wrap;
				gap: 1px;
				background-color: var(--color-border);
				.location-restriction {
					color: var(--color-text);
					background-color: var(--color-background);
					outline: none;
					position: relative;
					text-decoration: none;
					transition: background 0.2s linear;
					flex-grow: 1;
					text-align: center;
					/* padding: .4em 0; */
					/* border-right: 1px solid var(--color-border); */
					&:after,
					&:before {
						background-color: var(--color-background);
						bottom: 0;
						clip-path: polygon(50% 50%, -50% -50%, 0 100%);
						content: "";
						left: 100%;
						position: absolute;
						top: 0;
						transition: background 0.2s linear;
						width: 1.4em;
						z-index: 1;
					}
					&:before {
						background: var(--color-border);
						margin-left: 2px;
					}
					&:last-child {
						border-right: none;
					}
					&.enabled, &.enabled:after {
						background-color: var(--color-highlight);
						color: var(--color-highlight-text);
					}
					&.explicitly-enabled {
						text-decoration: underline;
					}
					&.explicitly-disabled {
						text-decoration: line-through;
					}
				}
			}
			.edit-trait-id {
				display: flex;
				margin: 1em;
				.edit-trait-label {
					border-right: 1px solid var(--color-border);
					padding: .4em;
					display: flex;
					align-items: center;
				}
				.edit-trait-selector {
					padding: .4em;
				}
			}
			.edit-statement {
				position: relative;
				.statement-edit {
					font-size: 1.2em;
					resize: vertical;
					overflow: hidden;
					padding-right: 1em;
				}
				.statement-length {
					position: absolute;
					right: 0;
					top: 2px;
					width: 3em;
					text-align: center;
					font-size: .8em;
					text-shadow: var(--text-shadow);
					background-image: linear-gradient(45deg, transparent 0%, var(--color-background) 100%);
					&.exceeded {
						color: red;
					}
				}
				.statement-examples {
					display: flex;
					flex-direction: column;
					align-items: flex-start;
					max-width: fit-content;
					width: 80%;
					.statement-example {
						padding: .4em 0;
						border: 1px solid var(--color-border);
						text-align: left;
					}
				}
			}
			.edit-notes {
				.notes {
					min-width: 100%;
					max-width: fit-content;
					min-height: 12em;
				}
			}
			.show-character {
				.show-character-list {
					.character-list {
						display: flex;
						flex-wrap: wrap;
						align-items: center;
						gap: .4em;
					}
				}
			}
			.add-sfx-list {
				display: flex;
				flex-wrap: wrap;
				gap: .4em;
				.add-sfx {
					/* display: inline-block; */
				}
			}
			.create-sfx {
				display: flex;
				flex-direction: column;
				gap: .4em;
				padding: 1em;
					.add-sfx-title {
						font-weight: bold;
					}
					.add-sfx-description {
						border-top: 1px solid var(--color-border);
						max-width: 100%;
						min-height: 6em;
					}
			}
		}
	}
	.trait.clickable {
		cursor: pointer;
	}
	.without-statement .trait-name.label {
		font-size: 1.2em;
	}
	.with-statement .trait-name.label {
		font-weight: bold;
		line-height: 1em;
	}
</style>

<style>
	.touch {
		.trait {
			/* height: 50vh; */
			.trait-inner {
				overflow-y: visible;
			}
		}
	}
	.kbm {
		.trait {
			width: 100%;
		}
	}
	@keyframes moveGradient {
		50% {
			background-position: 100% 50%;
		}
	}
	.dark {
		.trait {
			/* flex-grow: 1; */
			scroll-snap-align: center;
			width: 85%;
			.trait-inner {
				border-radius: 10px;
				/* max-height: 50vh; */
				height: 100%;
				overflow-y: auto;
				display: flex;
				flex-direction: column;
				justify-content: space-between;
			}
			/* margin: .6em .4em; */
			border-radius: 10px;
			/* flex-grow: 0.6; */
			text-shadow: none;
			.descriptor {
				/* padding: 0 1em; */
				overflow: hidden;
				.rating {
					margin-left: .2em;
				}
				.trait-name {
					margin-left: .6em;
				}
				.statement {
					padding-left: .6em;
				}
				.trait-image {
					transform: translateX(-.8em) translateY(-.6em);
					position: relative;
					width: 70px;
					.trait-to-entity {
						position: absolute;
						height: 120px;
					}
				}
			}
			.explanation {
				box-shadow: inset 0 0 10px var(--color-border);
				padding: 1em;
				width: 80%;
				text-align: center;
				background-color: var(--color-border);
				color: var(--color-disabled);
				margin: .4em 10%;
				font-style: italic;
			}
			.notes {
				font-style: italic;
				font-size: .8em;
				padding: 0.4em 4em;
				color: var(--color-disabled);
				/* box-shadow: inset 0 0 10px var(--color-border); */
				background-image: linear-gradient(to bottom, var(--color-border) -100%, transparent 30%);
			}
			.statement {
				font-style: italic;
				font-size: 1.2em;
				padding-left: 1em !important;
			}
			.rating.take-resource {
				box-shadow: inset 0 0 10px var(--color-highlight);
				border: 1px solid var(--color-highlight);
				border-radius: 10px;
				background-color: var(--color-background-mute);
				/* margin-top: -.4em;
				margin-bottom: .4em; */
				transform: translateY(-.4em) translateX(.4em);
			}
			.sub-traits {
				border-top: 1px solid var(--color-border);
			}
			.edit-buttons {
				border-top: 1px solid var(--color-editing);
				border-radius: 0 0 10px 10px;
				overflow: hidden;
				.button-mnml {
					background-color: transparent;
				}
				.play-button {
					box-shadow: inset 0 0 80px var(--color-highlight);
					text-shadow: 0 0 20px var(--color-highlight);
				}
				.save-button {
					box-shadow: inset 0 0 80px var(--color-highlight);
					text-shadow: 0 0 20px var(--color-highlight);
				}
				.save-temp-button {
					box-shadow: inset 0 0 80px var(--color-editing);
					text-shadow: 0 0 20px var(--color-editing);
				}
				.edit-button {
					box-shadow: inset 0 0 80px var(--color-editing);
					text-shadow: 0 0 20px var(--color-editing);
				}
				.cancel-button {
					box-shadow: inset 0 0 80px var(--color-background);
					text-shadow: 0 0 20px var(--color-background);
				}
				.remove-button {
					box-shadow: inset 0 0 80px var(--color-hitch);
					text-shadow: 0 0 20px var(--color-hitch);
				}
			}
			&.with-statement {
				/* font-size: .8em; */
			}
			&.inactive {
				&.positive {
					&.d4:not(.empty) {
						.trait-inner {
							background-image: linear-gradient(215deg,
								var(--color-positive-die-4) -100%,
								var(--color-background-mute) 50%);
						}
						border-left: 1px solid var(--color-positive-die-4);
						border-right: 1px solid var(--color-positive-die-4);
						border-color: var(--color-positive-die-4);
						.sfxs {
							border-top: 1px solid var(--color-positive-die-4);
						}
						&:hover {
							.trait-inner {
								background-image: linear-gradient(215deg,
									var(--color-positive-die-4) -50%,
									var(--color-background) 80%);
							}
						}
					}
					&.d6:not(.empty) {
						.trait-inner {
							background-image: linear-gradient(215deg,
								var(--color-positive-die-6) -100%,
								var(--color-background-mute) 50%);
						}
						border-left: 1px solid var(--color-positive-die-6);
						border-right: 1px solid var(--color-positive-die-6);
						border-color: var(--color-positive-die-6);
						.sfxs {
							border-top: 1px solid var(--color-positive-die-6);
						}
						&:hover {
							.trait-inner {
								background-image: linear-gradient(215deg,
									var(--color-positive-die-6) -50%,
									var(--color-background) 80%);
							}
						}
					}
					&.d8:not(.empty) {
						.trait-inner {
							background-image: linear-gradient(215deg,
								var(--color-positive-die-8) -100%,
								var(--color-background-mute) 50%);
						}
						border-left: 1px solid var(--color-positive-die-8);
						border-right: 1px solid var(--color-positive-die-8);
						border-color: var(--color-positive-die-8);
						.sfxs {
							border-top: 1px solid var(--color-positive-die-8);
						}
						&:hover {
							.trait-inner {
								background-image: linear-gradient(215deg,
									var(--color-positive-die-8) -50%,
									var(--color-background) 80%);
							}
						}
					}
					&.d10:not(.empty) {
						.trait-inner {
							background-image: linear-gradient(215deg,
								var(--color-positive-die-10) -100%,
								var(--color-background-mute) 50%);
						}
						border-left: 1px solid var(--color-positive-die-10);
						border-right: 1px solid var(--color-positive-die-10);
						border-color: var(--color-positive-die-10);
						.sfxs {
							border-top: 1px solid var(--color-positive-die-10);
						}
						&:hover {
							.trait-inner {
								background-image: linear-gradient(215deg,
									var(--color-positive-die-10) -50%,
									var(--color-background) 80%);
							}
						}
					}
					&.d12:not(.empty) {
						.trait-inner {
							background-image: linear-gradient(215deg,
								var(--color-positive-die-12) -100%,
								var(--color-background-mute) 50%);
						}
						border-left: 1px solid var(--color-positive-die-12);
						border-right: 1px solid var(--color-positive-die-12);
						border-color: var(--color-positive-die-12);
						.sfxs {
							border-top: 1px solid var(--color-positive-die-12);
						}
						&:hover {
							.trait-inner {
								background-image: linear-gradient(215deg,
									var(--color-positive-die-12) -50%,
									var(--color-background) 80%);
							}
						}
					}
				}
				&.negative {
					&.d4:not(.empty) {
						.trait-inner {
							background-image: linear-gradient(45deg,
								var(--color-negative-die-4) -100%,
								var(--color-background-mute) 50%);
						}
						border-left: 1px solid var(--color-negative-die-4);
						border-right: 1px solid var(--color-negative-die-4);
						border-color: var(--color-negative-die-4);
						.sfxs {
							border-top: 1px solid var(--color-negative-die-4);
						}
						&:hover {
							.trait-inner {
								background-image: linear-gradient(45deg,
									var(--color-negative-die-4) -50%,
									var(--color-background) 80%);
							}
						}
					}
					&.d6:not(.empty) {
						.trait-inner {
							background-image: linear-gradient(45deg,
								var(--color-negative-die-6) -100%,
								var(--color-background-mute) 50%);
						}
						border-left: 1px solid var(--color-negative-die-6);
						border-right: 1px solid var(--color-negative-die-6);
						border-color: var(--color-negative-die-6);
						.sfxs {
							border-top: 1px solid var(--color-negative-die-6);
						}
						&:hover {
							.trait-inner {
								background-image: linear-gradient(45deg,
									var(--color-negative-die-6) -50%,
									var(--color-background) 80%);
							}
						}
					}
					&.d8:not(.empty) {
						.trait-inner {
							background-image: linear-gradient(45deg,
								var(--color-negative-die-8) -100%,
								var(--color-background-mute) 50%);
						}
						border-left: 1px solid var(--color-negative-die-8);
						border-right: 1px solid var(--color-negative-die-8);
						border-color: var(--color-negative-die-8);
						.sfxs {
							border-top: 1px solid var(--color-negative-die-8);
						}
						&:hover {
							.trait-inner {
								background-image: linear-gradient(45deg,
									var(--color-negative-die-8) -50%,
									var(--color-background) 80%);
							}
						}
					}
					&.d10:not(.empty) {
						.trait-inner {
							background-image: linear-gradient(45deg,
								var(--color-negative-die-10) -100%,
								var(--color-background-mute) 50%);
						}
						border-left: 1px solid var(--color-negative-die-10);
						border-right: 1px solid var(--color-negative-die-10);
						border-color: var(--color-negative-die-10);
						.sfxs {
							border-top: 1px solid var(--color-negative-die-10);
						}
						&:hover {
							.trait-inner {
								background-image: linear-gradient(45deg,
									var(--color-negative-die-10) -50%,
									var(--color-background) 80%);
							}
						}
					}
					&.d12:not(.empty) {
						.trait-inner {
							background-image: linear-gradient(45deg,
								var(--color-negative-die-12) -100%,
								var(--color-background-mute) 50%);
						}
						border-left: 1px solid var(--color-negative-die-12);
						border-right: 1px solid var(--color-negative-die-12);
						border-color: var(--color-negative-die-12);
						.sfxs {
							border-top: 1px solid var(--color-negative-die-12);
						}
						&:hover {
							.trait-inner {
								background-image: linear-gradient(45deg,
									var(--color-negative-die-12) -50%,
									var(--color-background) 80%);
							}
						}
					}
				}
			}
			&.hidden {
				opacity: .8;
				.trait-inner {
					box-shadow: inset 0 0 20px var(--color-disabled);
					/* padding: 10px; */
				}
			}
		}
		.trait.dis {
			.trait-inner {
				background-image: linear-gradient(45deg,
					var(--color-disabled) -100%,
					var(--color-background) 50%);
			}
			border-left: 1px solid var(--color-disabled);
			border-right: 1px solid var(--color-disabled);
			border-color: var(--color-disabled);
			.sfxs {
				border-top: 1px solid var(--color-disabled);
			}
			&:hover {
				.trait-inner {
					background-image: linear-gradient(45deg,
						var(--color-disabled) -50%,
						var(--color-background) 80%);
				}
			}
		}
		.trait.empty {
			/* .trait-inner {
				background-image: linear-gradient(45deg,
					var(--color-background-soft) -100%,
					var(--color-background) 50%);
			}
			border-left: 1px solid var(--color-background-soft);
			border-right: 1px solid var(--color-background-soft);
			border-color: var(--color-background-soft);
			.sfxs {
				border-top: 1px solid var(--color-background-soft);
			}
			&:hover {
				.trait-inner {
					background-image: linear-gradient(45deg,
						var(--color-background-soft) -50%,
						var(--color-background) 80%);
				}
			} */
			/* text-shadow: var(--text-shadow); */
			box-shadow: 0 0 10px var(--color-background-mute);
			background-color: var(--color-background-mute);
		}
		.trait.challenge {
			--border-width: 1px;
			position: relative;
			.trait-inner {
				background-color: var(--color-background);
				z-index: 1;
				margin: 1px;
			}
			&.active.positive .trait-inner {
				background-image: linear-gradient(235deg,
					var(--color-highlight) -20%,
					var(--color-background) 150%);
			}
			&.active.negative .trait-inner {
				background-image: linear-gradient(45deg,
					var(--color-highlight) -20%,
					var(--color-background) 150%);
			}
			&::before {
				position: absolute;
				content: "";
				border-radius: 10px;
				top: calc(-1 * var(--border-width));
				left: calc(-1 * var(--border-width));
				z-index: 0;
				width: calc(100% + var(--border-width) * 2);
				height: calc(100% + var(--border-width) * 2);
				background: linear-gradient(
					60deg,
					hsl(224, 85%, 66%),
					hsl(269, 85%, 66%),
					hsl(314, 85%, 66%),
					hsl(359, 85%, 66%),
					hsl(44, 85%, 66%),
					hsl(89, 85%, 66%),
					hsl(134, 85%, 66%),
					hsl(179, 85%, 66%)
				);
				background-size: 300% 300%;
				background-position: 0 50%;
				animation: moveGradient 2s alternate infinite;
			}
		}
		.trait.resource {
			border-style: dashed;
			border-color: var(--color-border);
		}
		.trait.active {
			background-color: var(--color-highlight);
			border-left: 1px solid var(--color-highlight);
			border-right: 1px solid var(--color-highlight);
			.sfxs {
				border-top: 1px solid var(--color-highlight);
			}
			text-shadow: var(--text-shadow);
			&.positive {
				background-image: linear-gradient(235deg,
					var(--color-highlight) -20%,
					var(--color-background) 150%);
			}
			&.negative {
				background-image: linear-gradient(45deg,
					var(--color-highlight) -20%,
					var(--color-background) 150%);
			}
		}
		.trait.editing {
			background-image: linear-gradient(45deg,
				var(--color-editing) -20%,
				var(--color-background) 70%);
			border-left: 1px solid var(--color-editing);
			border-right: 1px solid var(--color-editing);
			width: 100%;
			height: 100%;
			.statement.statement-edit {
				font-size: 2em;
			}
			.sfxs {
				border-top: 1px solid var(--color-editing);
			}
			.changed {
				border: 1px solid red;
			}
			.edit-setting-buttons {
				border-top: 1px solid var(--color-border);
				border-left: 1px solid var(--color-border);
				border-right: 1px solid var(--color-border);
				border-top-left-radius: 10px;
				border-top-right-radius: 10px;
				background-color: transparent;
				position: sticky;
				top: 0;
				z-index: 2;
				.divider {
					border-left: 1px solid var(--color-border);
				}
				.button-mnml.active {
					background-color: var(--color-background-mute);
				}
			}
		}
		.viewing {
			/* flex-grow: 1; */
			width: 100%;
			height: 100%;
		}
		.sfxs {
			border-top: 1px solid var(--color-border);
		}
	}
	.light {
		.trait {
			/* margin: 1px 0; */
			/* margin-bottom: .8em; */
			border-top: 1px solid var(--color-border);
			border-bottom: 1px solid var(--color-border);
			flex-grow: 1;
			background-color: var(--color-background);
			.descriptor {
				flex-grow: 1;
			}
			.trait-name.label {
				border-bottom: 1px dashed var(--color-border);
			}
			.explanation.label {
				font-style: italic;
				font-size: .8em;
			}
			.statement {
				font-family: 'Courier New', Courier, monospace;
				font-size: 1.4em;
				background-color: var(--color-background-soft);
				color: var(--color-text);
				text-align: center;
				padding-right: .5em;
			}
			.rating {
				flex-grow: 0;
				&.take-resource {
					border: 1px solid var(--color-highlight);
					padding: 0 1em;
					background-color: var(--color-background);
				}
			}
			.explanation,
			.sfxs,
			.notes {
				margin-left: 1.4em;
			}
			.sfxs {
				flex-grow: 1;
			}
			&.negative {
				color: var(--color-hitch);
			}
			&.challenge {
				.trait-inner {
					margin: 3px -1px !important;
				}
			}
			&.active {
				background-color: var(--color-highlight);
				color: var(--color-highlight-text);
				.statement {
					background-color: var(--color-highlight);
					color: var(--color-highlight-text);
					font-size: 1.8em;
				}
			}
			&.editing {
				background-color: var(--color-editing);
				border-top: 2px dotted var(--color-border);
				border-bottom: 2px dotted var(--color-border);
				.edit-setting-buttons {
					border: 1px dashed var(--color-border);
					.divider {
						border-left: 1px dashed var(--color-border);
					}
				}
				.edit-buttons {
					border-top: 1px dashed var(--color-border);
				}
			}
			&.viewing {
				border-bottom: 1px solid var(--color-border);
				padding: 1em 0 2em 0;
			}
			&.with-statement {
				.trait-name.label {
					padding-top: .4em;
					padding-left: 1em;
				}
			}
			&.without-statement {
				.trait-name.label {
					font-size: 1.6em;
					padding-left: 1em;
				}
			}
			&.dim {
				display: none;
			}
		}
		.trait-divider {
			margin: .8em 0;
		}
	}
</style>
