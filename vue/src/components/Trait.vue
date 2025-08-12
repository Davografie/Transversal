<script setup lang="ts">
	import _ from 'lodash'
	import { marked } from 'marked'

	import { ref, type Ref, computed, watch } from 'vue'

	import useClipboard from 'vue-clipboard3'
	const { toClipboard } = useClipboard()
	const copy_id = async () => {
		try {
			await toClipboard(trait.value.traitSettingId ?? trait.value.id)
			console.log('Copied to clipboard')
		} catch (e) {
			console.error(e)
		}
	}

	import { usePreferredColorScheme } from '@vueuse/core'

	const preferredColor = usePreferredColorScheme()

	import { useDicepool } from '@/composables/Dicepool'

	import Rating from '@/components/Rating.vue'
	import RatingEdit from '@/components/RatingEdit.vue'
	import DiePicker from '@/components/DiePicker.vue'
	import SFX from '@/components/SFX.vue'
	import SubTrait from '@/components/SubTrait.vue'
	import EntityCard from './EntityCard.vue'

	import { usePlayer } from '@/stores/Player'
	
	import { useTrait, rating_types } from '@/composables/Trait'
	import { useDie } from '@/composables/Die'
	import { useSFXList } from '@/composables/SFXList'
	import { useLocation } from '@/composables/Location'

	import type { Die as DieType, SFX as SFXType, Trait } from '@/interfaces/Types'

	const props = defineProps<{
		trait?: Trait,
		trait_id: string,
		traitset_id?: string,
		trait_setting_id?: string,
		entity_id?: string,
		edit_mode?: boolean,
		viewing?: boolean,
		highlight_root_id?: string,
		highlighted?: boolean,
		location_key?: string,
		traitset_limit?: number
	}>()

	const emit = defineEmits([
		'refetch',
		'next_traitset',
		'require_traits',
		'set_highlight',
		'kill_highlight'
	])

	const player = usePlayer()

	const {
		trait,
		retrieve_trait,
		retrieve_trait_setting,
		mutate_trait,
		mutate_trait_setting,
		overwrite_trait,
		copy_trait,
		unassign_trait,
		assign_subtrait,
		unassign_subtrait,
		retrieve_statement_examples,
		change_trait_entity,
		transfer_resource
	} = useTrait(props.trait, props.trait_id, props.trait_setting_id, props.entity_id)
	
	retrieve_trait()

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
	} = useDicepool()

	const {
		location,
		set_location_key,
		retrieve_location,
		retrieve_presence,
		retrieve_parents
	} = useLocation(undefined, props.location_key)

	// enable/disable trait edit mode
	const mode = ref('neutral')

	// true for longtaps so that normal taps/clicks don't trigger
	const held = ref(false)

	// placeholders for mutating trait
	const new_rating: Ref<DieType[]> = ref(trait.value.rating ?? [])
	const new_ratingType: Ref<string> = ref(trait.value.ratingType ?? 'empty')
	const new_statement: Ref<string> = ref(trait.value.statement ?? "")
	const new_hidden: Ref<boolean> = ref(trait.value.traitSetting?.hidden ?? false)
	const new_notes: Ref<string> = ref(trait.value.notes ?? "")
	const new_sfxs: Ref<SFXType[]> = ref(trait.value.sfxs ?? [])
	const new_locationsEnabled: Ref<string[]> = ref(trait.value.traitSetting?.locationsEnabled ?? [])
	const new_locationsDisabled: Ref<string[]> = ref(trait.value.traitSetting?.locationsDisabled ?? [])

	function switch_to_editing() {
		reset_temporary_attributes()
		if(props.location_key) set_location_key(props.location_key)
		retrieve_location()
		retrieve_trait_setting()
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
		edit_statement.value = trait.value.statement || trait.value.notes ? true : false
		edit_notes.value = trait.value.notes ? true : false
		edit_rating.value = false
		add_subtraits.value = false
		show_sfxs.value = false
		mode.value = 'editing'
		if(
			player.is_gm
			|| props.entity_id == player.player_character.id
			|| props.entity_id?.startsWith('Relations/')
		) {
			can_edit.value = true
		}
	}

	const can_edit = ref<boolean>(false)

	function reset_temporary_attributes() {
		new_rating.value = trait.value?.rating ?? []
		new_ratingType.value = trait.value?.ratingType ?? 'empty'
		new_statement.value = trait.value?.statement ?? ""
		new_notes.value = trait.value?.notes ?? ""
		new_sfxs.value = trait.value?.sfxs ?? []
		new_hidden.value = trait.value?.traitSetting?.hidden ?? false
		new_locationsEnabled.value = trait.value?.traitSetting?.locationsEnabled ?? []
		new_locationsDisabled.value = trait.value?.traitSetting?.locationsDisabled ?? []
	}

	// watch(trait, () => {
	// 	reset_temporary_attributes()
	// })

	watch(() => props.edit_mode, () => {
		if (props.edit_mode) {
			switch_to_editing()
		}
		else {
			mode.value = 'neutral'
		}
	})

	function click_trait() {
		/* add trait to dicepool */
		if(
			// long pressing the trait enables viewing mode
			!held.value
			// dim all traits that don't have highlight when highlight is set
			// && !(props.highlight_root_id && !props.highlighted && !trait.value.requiredTraits?.map((t) => t.id).includes(props.highlight_root_id ?? ''))
		) {
			// when the player is in edit mode they can change the trait
			if (props.edit_mode && mode.value != 'editing') {
				switch_to_editing()
			}
			// otherwise add the trait to the dicepool
			else if(
				// traits without rating have no business here
				trait.value.rating
				// clicking the trait while editing shouldn't do anything
				&& mode.value != 'editing'
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
					&& !traitset_limit_reached()
					// traitset dice limit isn't reached
					// && traitset_dice(props.traitset_id ?? '').filter((d) => d.entityId == props.entity_id).length < (props.traitset_limit ?? 0)
				) {
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
								|| (player.the_entity && props.entity_id != player.the_entity?.id)
							) {
								add_die(_.clone(die))
							}
							else {
								add_complication(_.clone(die))
							}
						}
					}
					// check if trait has any negative subtraits, they should be added as complications
					if(trait.value.subTraits && trait.value.subTraits?.length > 0) {
						for(const subtrait of trait.value.subTraits) {
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
					if(traitset_limit_reached()) {
						emit('next_traitset')
					}
				}
				else if(check_trait(trait.value.traitSettingId ?? '')) {
					remove_traitsetting_dice(props.trait_setting_id ?? '')
					remove_complication_by_traitsetting(props.trait_setting_id ?? '')
					if(trait.value.subTraits && trait.value.subTraits?.length > 0) {
						for(const subtrait of trait.value.subTraits) {
							remove_traitsetting_dice(trait.value.traitSettingId ?? '')
							remove_complication_by_traitsetting(trait.value.traitSettingId ?? '')
						}
					}
				}
			}
			// in case of resource and all rating die types are the same, decrease that by one
			else if(
				// traits without rating have no business here
				trait.value.rating
				// clicking the trait while editing shouldn't do anything
				&& mode.value != 'editing'
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
				trait.value.ratingType == 'empty'
				&& check_trait(trait.value.traitSettingId ?? '')
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

	function click_subtrait(subtrait: Trait) {
		if (player.editing && mode.value != 'editing') {
			click_trait()
		}
		
		// add subtrait to the dicepool
		else if(
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
							!traitset_limit_reached()
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
			if(traitset_limit_reached()) {
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
	}

	const traitset_limit_reached = () => {
		// trait traitset limit
		return [...new Set(traitset_dice(props.traitset_id ?? '').filter((d) => d.entityId == props.entity_id).map((d) => d.traitsettingId))].length >= (props.traitset_limit ?? 0)
		// dice traitset limit
		// return traitset_dice(props.traitset_id ?? '').filter((d) => d.entityId == props.entity_id).length < (props.traitset_limit ?? 1)
	}

	function longtap_trait(e: MouseEvent) {
		e.stopPropagation()
		held.value = true
		console.log("longtap")
		if(
			mode.value != 'editing'
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

	function deplete_resource(dc: DieType) {
		if(
			mode.value != 'editing'
			&& trait.value.rating?.map((d) => d.id).includes(dc.id)
			&& inAddingPhase.value
		) {
			new_rating.value = trait.value.rating.filter((d) => d.id != dc.id)
			mutate_trait_setting({ 'rating': new_rating.value.map((r) => r.number_rating) })
			// const { die } = useDie({rating: dc})
			dc.traitId = trait.value.id
			if(props.traitset_id) dc.traitsetId = props.traitset_id
			if(props.entity_id) dc.entityId = props.entity_id
			if(props.trait_setting_id) dc.traitsettingId = props.trait_setting_id
			if(dc.number_rating > 0) {
				add_die(_.clone(dc))
				change_result_limit(1)
			}
			else {
				add_complication(_.clone(dc))
			}
		}
		else if(mode.value == 'editing' && !transfer_resource_mode.value) {
			edit_rating.value = true
		}
		else if(mode.value == 'editing' && transfer_resource_mode.value && player.the_entity && props.entity_id != player.the_entity?.id) {
			// take resource from environment
			console.log("take resource from environment: " + JSON.stringify(dc))
			transfer_resource(player.the_entity.id, dc)
		}
		else if(mode.value == 'editing' && transfer_resource_mode.value && player.the_entity && player.the_entity.location?.id && props.entity_id == player.the_entity?.id) {
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
	function change_trait() {
		if(inherited.value) {
			overwrite_trait({
				'ratingType': new_ratingType.value,
				'rating': new_rating.value.map((r) => r.number_rating),
				'statement': new_statement.value,
				'notes': new_notes.value,
				'sfxs': new_sfxs.value.map((sfx) => sfx.id),
				'locationsEnabled': new_locationsEnabled.value,
				'locationsDisabled': new_locationsDisabled.value,
				'inheritedAs': trait.value.traitSetting?.id ?? trait.value.traitSettingId ?? props.trait_setting_id
			})
		}
		else {
			mutate_trait_setting({
				'ratingType': new_ratingType.value,
				'rating': new_rating.value.map((r) => r.number_rating),
				'statement': new_statement.value,
				'notes': new_notes.value,
				'sfxs': new_sfxs.value.map((sfx) => sfx.id),
				'locationsEnabled': new_locationsEnabled.value,
				'locationsDisabled': new_locationsDisabled.value
			})
		}
		mode.value = 'neutral'
		setTimeout(() => {
			refetch(); retrieve_trait()
		}, 200)
	}

	function cancel_edit() {
		retrieve_trait()
		mode.value = 'neutral'
	}

	function delete_trait() {
		unassign_trait()
		refetch()
	}

	function refetch() {
		setTimeout(() => emit('refetch'), 200)
	}

	const edit_statement = ref(trait.value.statement || trait.value.notes ? true : false)
	const edit_notes = ref(trait.value.notes ? true : false)
	
	const statement_examples = ref<string[]>([])
	const show_statement_examples = ref(false)
	async function display_statement_examples() {
		console.log("displaying statement examples")
		let temp = await retrieve_statement_examples()
		statement_examples.value = _.clone(temp).sort(() => 0.5 - Math.random())
		show_statement_examples.value = true
	}
	const rendered_statement = computed(
		() => trait.value.statement ? marked.parse(trait.value.statement) : ''
	)

	const inherited = computed(() => {
		return trait.value.traitSetting?.fromEntity?.id != props.entity_id
	})


	// SFX stuff
	const { sfx_list, create_sfx, retrieve_sfx_list } = useSFXList()

	const edit_rating = ref(false)
	const show_sfxs = ref(false)
	const selected_sfx = ref<SFXType>({} as SFXType)
	const expanded_sfx = ref<SFXType>({} as SFXType)
	const show_add_sfx = ref(false)
	const new_sfx_name = ref<string>('')
	const new_sfx_description = ref<string>('')

	function toggle_sfxs(event: MouseEvent) {
		event.stopPropagation()
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
        // mutate_trait({ 'sfxs': new_sfxs.value.filter(sfx => sfx.id != sfx_id).map(sfx => sfx.id) })
		// retrieve_trait()
		new_sfxs.value = new_sfxs.value.filter(sfx => sfx.id != sfx_id)
		expanded_sfx.value = {} as SFXType
    }

	function create_new_sfx() {
		create_sfx(new_sfx_name.value, new_sfx_description.value)
		new_sfx_name.value = ''
		new_sfx_description.value = ''
		show_add_sfx.value = false
		setTimeout(retrieve_sfx_list, 200)
	}


	function die_picker_pick(rating: DieType[]) {
		console.log("die picker picked: " + JSON.stringify(rating))
		new_rating.value = rating
		change_trait()
	}

	function change_rating(rating_type: string, rating: DieType[]) {
		new_ratingType.value = rating_type
		new_rating.value = rating
		// change_trait()
	}

	watch(() => player.editing, (newVal) => {
		if (!newVal) {
			mode.value = 'neutral';
		}
	})


	const add_subtraits = ref(false)
	function add_subtrait(subtrait: Trait) {
		if(trait.value.traitSettingId && !trait.value.subTraits?.map((x) => x.id).includes(subtrait.id)) {
			assign_subtrait(trait.value.traitSettingId, subtrait.id)
		}
		retrieve_trait()
	}
	function remove_subtrait(subtrait: Trait) {
		if(subtrait.traitSettingId) {
			unassign_subtrait(subtrait.traitSettingId)
		}
		retrieve_trait()
	}


	// change rating type
	function increase_rating_type() {
		// cycles through rating types to change trait rating type
		if(new_ratingType.value) {
			new_ratingType.value = rating_types[(rating_types.findIndex(x => x == new_ratingType.value) + 1) % rating_types.length]
		}
		else {
			// sometimes the ratingType is null, so it needs to be created
			new_ratingType.value = rating_types[0]
		}
		mutate_trait({ 'ratingType': new_ratingType.value })
	}

	function decrease_rating_type() {
		// cycles through rating types to change trait rating type
		if(new_ratingType.value) {
			const index = rating_types.findIndex(x => x == new_ratingType.value) - 1;
			new_ratingType.value = rating_types[index < 0 ? rating_types.length - 1 : index];
		}
		else {
			// sometimes the ratingType is null, so it needs to be created
			new_ratingType.value = rating_types[0]
		}
		mutate_trait({ 'ratingType': new_ratingType.value })
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
		}
	}

	const isLocationEnabled = (location_id?: string, index?: number) => {
		return (
			(location_id && index)
			&& (
				trait.value.traitSetting?.locationsEnabled?.includes(location_id)
				|| isLocationEnabled(location.value.parents?.slice().reverse()[index - 1]?.id, index - 1)
			)
		) ?? false
	}

	const isLocationDisabled = (location_id?: string, index?: number) => {
		return (
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

	function steal() {
		if(props.traitset_id == 'Traitsets/3' && player.the_entity && props.entity_id != player.the_entity?.id) {
			change_trait_entity(player.the_entity.id)
			emit('refetch')
		}
		else if(props.traitset_id == 'Traitsets/3' && player.the_entity && player.the_entity?.location && props.entity_id == player.the_entity?.id) {
			change_trait_entity(player.the_entity.location?.id)
			emit('refetch')
		}
		else if(trait.value.ratingType == 'resource') {
			transfer_resource_mode.value = !transfer_resource_mode.value
		}
	}

	const transfer_resource_mode = ref(false)

	function copy() {
		copy_trait({
			'ratingType': new_ratingType.value,
			'rating': new_rating.value.map((r) => r.number_rating),
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
</script>

<template>
	<div class="trait" :class="[
				player.viewing ? 'viewing' : mode,
				in_dicepool ? 'active' : 'inactive',
				trait.ratingType ?? '',
				trait.statement ? 'with-statement' : 'without-statement',
				trait.ratingType != 'empty' && trait.rating && trait.rating.length > 0 && trait.rating[0].rating && trait.ratingType != 'empty' ? trait.rating[0].rating : 'empty',
				trait.ratingType != 'empty' && trait.rating && trait.rating.length > 0 && trait.rating[0].number_rating > 0 ? 'positive' : 'negative',
				trait.sfxs && trait.sfxs?.length > 0 ? 'with-sfxs' : 'without-sfxs',
				trait.subTraits && trait.subTraits?.length > 0 ? 'with-subtraits' : 'without-subtraits',
				props.highlighted || trait.requiredTraits?.map((t) => t.id).includes(props.highlight_root_id ?? '') ? 'highlighted' : '',
				// dim all traits that don't have highlight when highlight is set
				props.highlight_root_id && !props.highlighted && !trait.requiredTraits?.map((t) => t.id).includes(props.highlight_root_id ?? '') ? 'dim' : '',
				{ 'clickable': mode != 'editing' }
			]"
			v-if="trait"
			v-touch:hold="longtap_trait"
			@click.right="longtap_trait"
			@click="click_trait"
			@contextmenu="(e) => e.preventDefault()">
		
		<div class="trait-inner">

			
		<div class="descriptor" :class="[trait.statement ? 'with-statement' : 'without-statement',
					trait.sfxs && trait.sfxs?.length > 0 ? 'with-sfxs' : 'without-sfxs',]">
			<input type="button" class="button copy-id"
				title="copy traitsetting id"
				@click.stop="copy_id"
				value="#"
				v-if="player.is_gm && ['viewing', 'editing'].includes(mode)" />
			<div class="trait-text">
				<div class="label trait-name">
					<span>
						{{ trait.name }}
						<span class="label" v-if="mode == 'editing'
								&& inherited
								&& trait.traitSetting?.fromEntity?.name">
							{{ ' from ' + trait.traitSetting?.fromEntity?.name }}
						</span>
					</span>
					<span v-if="preferredColor == 'light'" class="label">
						{{ trait.ratingType ?? 'empty' }}
					</span>
				</div>
				<div class="label explanation" v-if="preferredColor == 'light' ||
													['viewing', 'editing'].includes(mode) ||
													player.viewing"
													v-html="marked(trait.explanation ?? '')">
				</div>
				<div class="statement" v-if="trait.statement && mode != 'editing'"
					v-html="rendered_statement" />

				<div class="edit-statement edit-attribute" v-if="edit_statement && mode == 'editing'">
					<div class="edit-statement-1">
						<input type="text" name="text-statement" ref="text-statement"
							class="statement statement-edit"
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
				<div class="notes" v-html="marked.parse(trait.notes)"
					v-if="trait.notes
					&& mode != 'editing'
					&& (player.is_gm
						|| props.entity_id == player.player_character.id
						|| props.entity_id?.startsWith('Relations/')
					)" />
				<div v-if="mode == 'viewing' || player.viewing" class="label">
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
					@click="(mode == 'editing' && !transfer_resource_mode && can_edit) ? edit_rating = true : undefined">
				<Rating v-if="trait.rating" :rating="trait.rating"
					:rating-type="trait.ratingType"
					@deplete-resource="deplete_resource"
					@deplete-challenge="(d) => mode == 'editing' ? edit_rating = true : deplete_challenge(d)" />
			</div>
		</div>

		<div class="edit-trait" v-if="mode == 'editing'">
			<div class="edit-setting-buttons" :class="{ 'small-buttons': player.small_buttons }">
				<input type="button" class="button-mnml"
					:value="player.small_buttons ? '#' : '#\ncopy ID'"
					title="copy traitsetting id"
					@click="copy_id"
					v-if="player.is_gm" />
				<input type="button" class="button-mnml"
					:class="edit_statement ? 'active' : 'inactive'"
					:value="edit_statement ?
							'📄\ncancel' :
							player.small_buttons ?
								'📄' :
								'📄\nstatement'"
					v-if="!trait.statement && can_edit"
					@click="() => {
						edit_statement = !edit_statement;
						new_statement = trait.statement ?? '';
					}" />
				<input type="button" class="button-mnml"
					:class="edit_notes ? 'active' : 'inactive'"
					:value="edit_notes ?
							'📄\ncancel' :
							player.small_buttons ?
								'📄' :
								'📄\nnotes'"
					v-if="!trait.notes && can_edit"
					@click="() => {
						edit_notes = !edit_notes;
						new_notes = trait.notes ?? '';
					}" />
				<input type="button" class="button-mnml"
					:class="edit_rating ? 'active' : 'inactive'"
					:value="player.small_buttons ? '🎲' :
						edit_rating ? '🎲\ncancel' : '🎲\nrating'"
					@click="edit_rating = !edit_rating"
					v-if="can_edit" />
				<input type="button" class="button-mnml subtrait-icon"
					:class="add_subtraits ? 'active' : 'inactive'"
					:value="add_subtraits ?
							'⪽\ncancel' :
							player.small_buttons ?
								'⪽' :
								'⪽\nadd subtrait'"
					v-if="trait.possibleSubTraits
						&& trait.possibleSubTraits?.filter((x) => !trait.subTraits?.map((y) => y.id).includes(x.id)).length > 0
						&& can_edit"
					@click="add_subtraits = !add_subtraits">
				<input type="button" class="button-mnml"
					:class="show_sfxs ? 'active' : 'inactive'"
					:value="show_sfxs ?
							'✨\ncancel' :
							player.small_buttons ?
								'✨' :
								'✨\nadd sfx'"
					@click="toggle_sfxs"
					v-if="sfx_list && sfx_list?.length > 0 && can_edit" />
				<input type="button" class="button-mnml"
					:class="transfer_resource_mode ? 'active' : 'inactive'"
					:value="player.small_buttons ?
						'🫳' : '🫳\n' + (props.entity_id != player.the_entity?.id ? ' take ' : ' drop ') + trait.name"
					:title="props.entity_id != player.the_entity?.id ? ' take ' : ' drop ' + trait.name"
					@click.stop="steal"
					v-if="trait.ratingType == 'resource' || props.traitset_id == 'Traitsets/3'" />
				<input type="button" class="button-mnml"
					:value="player.small_buttons ? '⧉' : '⧉\ncopy trait'"
					@click.stop="copy"
					v-if="player.is_gm" />
				<input type="button" class="button-mnml"
					:class="show_pc_visible ? 'active' : 'inactive'"
					:value="player.small_buttons ? '🧠' : '🧠\nshow PC'"
					@click.stop="show_pc_visible ? show_pc_visible = false : show_pcs()"
					@click.right="toggle_show_pc_visible"
					v-touch:hold="toggle_show_pc_visible"
					@contextmenu="(e) => e.preventDefault()"
					v-if="player.is_gm && can_edit" />
				<input type="button" class="button-mnml"
					:class="restrict_location ? 'active' : 'inactive'"
					:value="restrict_location ?
							'🗺\ncancel' :
							player.small_buttons ?
								'🗺' :
								'🗺\nrestrict by location'"
					@click="restrict_location = !restrict_location"
					v-if="can_edit && !props.entity_id?.startsWith('Relations/')" />
			</div>

			<div class="edit-rating edit-attribute" v-if="edit_rating">
				<!-- <span>trait type: </span>
				<input type="button" class="button" :value="rating_type_fix"
					@click="increase_rating_type"
					@click.right="decrease_rating_type" />
				<DiePicker v-if="['static', 'resource','challenge'].includes(new_ratingType ?? '')"
					:die="new_ratingType == 'static' && trait.rating ?
							trait.rating[0] :
							undefined"
					:dice="['resource','challenge'].includes(new_ratingType ?? '') && trait.rating ?
							trait.rating :
							undefined"
					:resource="['resource'].includes(trait.ratingType ?? '')"
					:preview="trait.ratingType != 'static'"
					@change-die="(rating: DieType[]) => die_picker_pick(rating)"
					@cancel="edit_rating = false" /> -->
				<RatingEdit
					v-if="trait.ratingType && trait.rating"
					:rating_type="new_ratingType"
					:rating="new_rating"
					@change-rating="(rating_type: string, rating: DieType[]) => change_rating(rating_type, rating)"
					@cancel="edit_rating = false" />
			</div>

			<div class="edit-notes edit-attribute" v-if="edit_notes">
				<textarea class="notes" v-model="new_notes" placeholder="notes" @contextmenu="(e) => e.stopPropagation()"
					v-if="player.is_gm || (props.entity_id == player.player_character.id || props.entity_id?.startsWith('Relations/'))" />
			</div>

			<div class="add-sub-traits edit-attribute"
					v-if="trait.possibleSubTraits
						&& trait.possibleSubTraits?.filter((x) => !trait.subTraits?.map((y) => y.id).includes(x.id)).length > 0
						&& mode == 'editing'
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
				<label for="hidden">hidden</label>
				<div class="show-character-list">
					<EntityCard
						v-for="entity_id in trait.traitSetting?.knownTo?.map((x) => x.id)" :key="entity_id"
						:entity_id="entity_id"
						:override_click="true"
						is_active
						@click_entity="toggle_known(entity_id)" />
					<EntityCard
						v-for="entity in showable_characters.filter((x) => !trait.traitSetting?.knownTo?.map((y) => y.id).includes(x.id))" :key="entity.id"
						:entity_id="entity.id"
						:override_click="true"
						:is_active="false"
						@click_entity="toggle_known(entity.id)" />
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

		<div class="sfxs" v-if="(trait.sfxs && trait.sfxs?.length > 0) || show_sfxs">
			<div v-if="(trait.sfxs && trait.sfxs?.length > 0 && !expanded_sfx.id)" class="sfx-sparkles section-icon">✨</div>
			<div class="sfx-list">
				<template v-for="(sfx, i) in (mode == 'editing' ? new_sfxs : trait.sfxs)" :key="sfx.id">
					<SFX :sfx_id="sfx.id" :trait-setting-id="trait.traitSettingId"
						@expand="expanded_sfx = sfx"
						@collapse="expanded_sfx = {} as SFXType"
						@activate="selected_sfx = sfx; click_trait()"
						@remove="remove_sfx(sfx.id)"
						:editing="mode == 'editing'"
						:adding="false"
						v-if="expanded_sfx.id ? sfx.id == expanded_sfx.id : true" />
					<!-- <span class="sfx-divider" v-if="(i < (trait.sfxs?.length ?? 0) - 1) && !expanded_sfx.id">/</span> -->
				</template>
			</div>
			<div class="add-sfx" v-if="mode == 'editing' && show_sfxs">
				<div class="add-sfx-list">
					<template v-for="(sfx, i) in sfx_list" :key="sfx.id">
						<SFX :sfx_id="sfx.id" :trait-setting-id="trait.traitSettingId"
							:editing="mode == 'editing'" @add="add_sfx(sfx)" adding />
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
				<div class="sub-traits-list">
					<template v-for="subtrait in trait.subTraits.filter((x) => x.rating?.reduce((a, b) => a + b.number_rating, 0) > 0)" :key="subtrait.traitSettingId">
						<SubTrait v-if="subtrait.traitSettingId"
							:trait_setting_id="subtrait.traitSettingId"
							:editing_trait="mode == 'editing'"
							:entity_id="props.entity_id"
							:parent_traitset_id="trait.traitsetId ?? trait.traitset?.id"
							@click_subtrait="click_subtrait(subtrait)"
							@remove_subtrait="remove_subtrait(subtrait)" />
					</template>
				</div>
			</div>
			<div>
				<div class="sub-traits-list">
					<template v-for="subtrait in trait.subTraits.filter((x) => x.rating?.reduce((a, b) => a + b.number_rating, 0) == 0)" :key="subtrait.traitSettingId">
						<SubTrait v-if="subtrait.traitSettingId"
							:trait_setting_id="subtrait.traitSettingId"
							:editing_trait="mode == 'editing'"
							:entity_id="props.entity_id"
							:parent_traitset_id="trait.traitsetId ?? trait.traitset?.id"
							@click_subtrait="click_subtrait(subtrait)"
							@remove_subtrait="remove_subtrait(subtrait)" />
					</template>
				</div>
			</div>
			<div>
				<div class="sub-traits-list">
					<template v-for="subtrait in trait.subTraits.filter((x) => x.rating?.reduce((a, b) => a + b.number_rating, 0) < 0)" :key="subtrait.traitSettingId">
						<SubTrait v-if="subtrait.traitSettingId"
							:trait_setting_id="subtrait.traitSettingId"
							:editing_trait="mode == 'editing'"
							:entity_id="props.entity_id"
							:parent_traitset_id="trait.traitsetId ?? trait.traitset?.id"
							@click_subtrait="click_subtrait(subtrait)"
							@remove_subtrait="remove_subtrait(subtrait)" />
					</template>
				</div>
			</div>
		</div>
		<div class="edit-buttons" :class="{ 'small-buttons': player.small_buttons }" v-if="mode == 'editing'">
			<input  type="button" class="button-mnml save-button"
				:value="player.small_buttons ? '💾' : '💾' + (inherited ? 'overwrite' : 'save') + ' trait'"
				@click.stop="change_trait"
				v-if="can_edit" />

			<input  type="button" class="button-mnml cancel-button"
				:value="player.small_buttons ? '✖' : '✖ cancel'"
				@click.stop="cancel_edit" />
				
			<input  type="button" class="button-mnml remove-button"
				:value="player.small_buttons ? '🗑' : '🗑 remove trait'"
				@click.stop="delete_trait"
				v-if="can_edit && !inherited" />
		</div>

		</div>
	</div>
</template>

<style scoped>
	.trait {
		text-align: left;
		display: flex;
		flex-direction: column;
		.traitset-name {
			font-size: small;
		}
		.descriptor {
			display: flex;
			flex-grow: 1;
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
		.explanation {
			font-size: .8em;
		}
		.statement {
			padding-left: .5em;
			width: 100%;
			/* max-height: 5em; */
			overflow: hidden;
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
			flex-grow: 1;
			.sfx-sparkles {
				position: absolute;
				left: 0;
				top: 2px;
			}
			.sfx-list {
				display: flex;
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
	}
	.trait.highlighted .trait-inner {
		border: 1px solid var(--color-highlight);
		color: var(--color-highlight-text);
		background-image: linear-gradient(45deg, var(--color-highlight) -20%,
							var(--color-background) 120%) !important;
	}
	.trait.editing {
		border-color: var(--color-highlight);
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: 1em;
		.edit-setting-buttons {
			display: flex;
			flex-wrap: wrap;
			gap: 1px;
			background-color: var(--color-border);
			border-color: var(--color-border-hover);
			overflow: hidden;
			.button-mnml {
				flex-grow: 1;
				padding: 1em .4em;
				background-color: var(--color-background);
				&.active {
					background-color: var(--color-editing);
					color: var(--color-editing-text);
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
				min-height: 4em;
			}
		}
		.edit-buttons {
			display: flex;
			min-height: 3em;
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
			.save-button {
				border-right: 1px solid var(--color-editing);
				background-color: var(--color-highlight);
				color: var(--color-highlight-text);
			}
			.cancel-button {
			}
			.remove-button {
				border-left: 1px solid var(--color-editing);
				background-color: var(--color-hitch);
				color: var(--color-hitch-text);
			}
		}
		.add-sfx-list {
			display: flex;
			flex-wrap: wrap;
			gap: .4em;
			.add-sfx {
				/* display: inline-block; */
				.add-sfx-title {
					font-weight: bold;
				}
				.add-sfx-description {
					border-top: 1px solid var(--color-border);
				}
			}
		}
		.create-sfx {
			display: flex;
			flex-direction: column;
			gap: .4em;
			padding: 1em;
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
		font-size: .8em;
		line-height: 1em;
	}
</style>

<style>
	@keyframes moveGradient {
		50% {
			background-position: 100% 50%;
		}
	}
	.dark {
		.trait {
			.trait-inner {
				border-radius: 10px;
				height: 100%;
			}
			/* margin: .6em .4em; */
			border-radius: 10px;
			flex-grow: 0.6;
			text-shadow: none;
			.descriptor {
				padding: 0 1em;
				.rating {
					margin-left: .2em;
				}
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
		}
		.trait.d4.positive.inactive {
			background-image: linear-gradient(215deg,
				var(--color-positive-die-4) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-positive-die-4);
			border-right: 1px solid var(--color-positive-die-4);
			border-color: var(--color-positive-die-4);
			.sfxs {
				border-top: 1px solid var(--color-positive-die-4);
			}
		}
		.trait.d6.positive.inactive {
			background-image: linear-gradient(215deg,
				var(--color-positive-die-6) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-positive-die-6);
			border-right: 1px solid var(--color-positive-die-6);
			border-color: var(--color-positive-die-6);
			.sfxs {
				border-top: 1px solid var(--color-positive-die-6);
			}
		}
		.trait.d8.positive.inactive {
			background-image: linear-gradient(215deg,
				var(--color-positive-die-8) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-positive-die-8);
			border-right: 1px solid var(--color-positive-die-8);
			border-color: var(--color-positive-die-8);
			.sfxs {
				border-top: 1px solid var(--color-positive-die-8);
			}
		}
		.trait.d10.positive.inactive {
			background-image: linear-gradient(215deg,
				var(--color-positive-die-10) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-positive-die-10);
			border-right: 1px solid var(--color-positive-die-10);
			border-color: var(--color-positive-die-10);
			.sfxs {
				border-top: 1px solid var(--color-positive-die-10);
			}
		}
		.trait.d12.positive.inactive {
			background-image: linear-gradient(215deg,
				var(--color-positive-die-12) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-positive-die-12);
			border-right: 1px solid var(--color-positive-die-12);
			border-color: var(--color-positive-die-12);
			.sfxs {
				border-top: 1px solid var(--color-positive-die-12);
			}
		}
		.trait.d4.negative.inactive {
			background-image: linear-gradient(45deg,
				var(--color-negative-die-4) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-negative-die-4);
			border-right: 1px solid var(--color-negative-die-4);
			border-color: var(--color-negative-die-4);
			.sfxs {
				border-top: 1px solid var(--color-negative-die-4);
			}
		}
		.trait.d6.negative.inactive {
			background-image: linear-gradient(45deg,
				var(--color-negative-die-6) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-negative-die-6);
			border-right: 1px solid var(--color-negative-die-6);
			border-color: var(--color-negative-die-6);
			.sfxs {
				border-top: 1px solid var(--color-negative-die-6);
			}
		}
		.trait.d8.negative.inactive {
			background-image: linear-gradient(45deg,
				var(--color-negative-die-8) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-negative-die-8);
			border-right: 1px solid var(--color-negative-die-8);
			border-color: var(--color-negative-die-8);
			.sfxs {
				border-top: 1px solid var(--color-negative-die-8);
			}
		}
		.trait.d10.negative.inactive {
			background-image: linear-gradient(45deg,
				var(--color-negative-die-10) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-negative-die-10);
			border-right: 1px solid var(--color-negative-die-10);
			border-color: var(--color-negative-die-10);
			.sfxs {
				border-top: 1px solid var(--color-negative-die-10);
			}
		}
		.trait.d12.negative.inactive {
			background-image: linear-gradient(45deg,
				var(--color-negative-die-12) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-negative-die-12);
			border-right: 1px solid var(--color-negative-die-12);
			border-color: var(--color-negative-die-12);
			.sfxs {
				border-top: 1px solid var(--color-negative-die-12);
			}
		}
		.trait.dis {
			background-image: linear-gradient(45deg,
				var(--color-disabled) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-disabled);
			border-right: 1px solid var(--color-disabled);
			border-color: var(--color-disabled);
			.sfxs {
				border-top: 1px solid var(--color-disabled);
			}
		}
		.trait.empty {
			background-image: linear-gradient(45deg,
				var(--color-background-soft) -100%,
				var(--color-background) 50%);
			border-left: 1px solid var(--color-background-soft);
			border-right: 1px solid var(--color-background-soft);
			border-color: var(--color-background-soft);
			.sfxs {
				border-top: 1px solid var(--color-background-soft);
			}
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
			.sfxs {
				border-top: 1px solid var(--color-editing);
			}
			.edit-trait {
				.edit-setting-buttons {
					border: 1px solid var(--color-border);
					border-radius: 10px;
					.divider {
						border-left: 1px solid var(--color-border);
					}
				}
			}
			.edit-buttons {
				border-top: 1px solid var(--color-editing);
				.save-button {
					border-radius: 0 0 0 10px;
				}
				.cancel-button {
					border-radius: 0;
				}
				.remove-button {
					border-radius: 0 0 10px 0;
				}
			}
		}
		.explanation {
			display: none;
		}
		.viewing .explanation, .editing .explanation {
			display: block;
		}
		.sfxs {
			border-top: 1px solid var(--color-border);
		}
	}
	.light {
		.trait {
			margin: .2em;
			/* margin-bottom: .8em; */
			flex-grow: 1;
			.descriptor {
				flex-grow: 1;
			}
			.trait-name.label {
				border-bottom: 1px dashed var(--color-border);
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
			.sfxs {
				margin-left: 1.4em;
			}
			&.negative {
				color: var(--color-hitch);
			}
			&.challenge {
				.trait-inner {
					margin: 3px -1px !important;
				}
			}
		}
		.trait-divider {
			margin: .8em 0;
		}
		.trait.active {
			background-color: var(--color-highlight);
			color: var(--color-highlight-text);
			.statement {
				background-color: var(--color-highlight);
				color: var(--color-highlight-text);
				font-size: 1.8em;
			}
		}
		.trait.editing {
			background-color: var(--color-editing);
			border-top: 2px dotted var(--color-border);
			border-bottom: 2px dotted var(--color-border);
			padding-top: .8em;
			.edit-trait {
				.edit-setting-buttons {
					border: 1px dashed var(--color-border);
					.divider {
						border-left: 1px dashed var(--color-border);
					}
				}
			}
			.edit-buttons {
				border-top: 1px dashed var(--color-border);
			}
		}
		.trait.viewing {
			border-bottom: 1px solid var(--color-border);
			padding: 1em 0 2em 0;
		}
		.trait.without-statement {
			.trait-name.label {
				font-size: 1.6em;
				padding-left: 1em;
			}
		}
		.trait.dim {
			display: none;
		}
	}
</style>
