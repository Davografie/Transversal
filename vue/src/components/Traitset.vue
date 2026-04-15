<script setup lang="ts">
	import _ from 'lodash'
	import { marked } from 'marked'

	import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
	import type { Ref } from 'vue'

	import Trait from '@/components/Trait.vue'
	import SFX from '@/components/SFX.vue'
	import TraitEdit from '@/components/TraitEdit.vue'
	import TraitLabel from '@/components/TraitLabel.vue'

	import { useTraitset, SORTING } from '@/composables/Traitset'
	import { useTraitList } from '@/composables/TraitList'
	import { view_modes } from '@/composables/Trait'
	import { useLocation } from '@/composables/Location'
	import { useEntity } from '@/composables/Entity'
	import { die_shapes } from '@/composables/Die'

	import type {
		SFX as SFXType,
		Trait as TraitType,
		Die as DieType,
		Entity as EntityType,
		Traitset
	} from '@/interfaces/Types'

	import { input_methods, usePlayerStore } from '@/stores/PlayerStore'
	import { useDicepool } from '@/composables/Dicepool'

	const props = defineProps<{
		traitset_id: string,
		entity_id: string,
		entity?: EntityType,
		relation_id?: string,
		limit?: number,
		expanded?: boolean,
		visible?: boolean,
		hide_title?: boolean,
		active?: boolean,
		next?: boolean,
		location_key?: string,
		extensible?: boolean,
		relationship?: boolean,
		location?: boolean,
		tutorial?: boolean,
		polling?: boolean,
		traitset?: Traitset
	}>()

	const emit = defineEmits(['next', 'set_traitset', 'unset_traitset', 'reset_scroll', 'show_entity'])
	// const emit = defineEmits<{
	// 	next: [],
	// 	set_traitset: [Traitset],
	// 	unset_traitset: [],
	// 	reset_scroll: [],
	// 	show_entity: [entity_id: string]
	// }>()

	const player = usePlayerStore()
	const { traitset_dice } = useDicepool(false)

	const {
		traitset,
		retrieve_traitset,
		retrieve_default_settings,
		create_trait,
		assign_trait,
		assign_locationrestricted_trait,
		set_entity,
		sorting,
		retrieve_traitset_setting,
		update_traitset_settings
	} = useTraitset(
		props.traitset,
		props.traitset_id,
		props.relation_id ?? props.entity_id,
		SORTING[0].id
	)

	const {
		traits: all_traits,
		retrieve_potential_traits: retrieve_all_traits
	} = useTraitList(
		undefined,
		props.traitset_id,
		undefined,
		false
	)


	onMounted(() => {
		// console.log("traitset " + traitset.value.name + " mounted")
		if(!got_traits_to_show.value && player.input_method == input_methods.kbm) {
			show_traits.value = false
		}
	})

	const polling_active = ref(props.polling ?? false)
	
	function polling() {
		if(polling_active.value && player.playing) {
			console.log("polling traitset " + traitset.value.name + " for entity " + props.entity_id)
			retrieve_traitset()
		}
		setTimeout(polling, 15000)
		// console.log("traitset polling disabled")
	}

	polling_active.value ? polling() : null

	onUnmounted(() => {
		polling_active.value = false
	})
	
	if(!props.traitset) await retrieve_traitset()
	retrieve_default_settings()

	const limiter: Ref<number> = ref(props.limit ?? traitset.value.limit ?? 1)

	const expanded_sfx: Ref<SFXType> = ref({} as SFXType)


	const held = ref(false)


	const show_info = ref(false)

	function title_longpress() {
		held.value = true
		show_info.value = !show_info.value
		if(show_info.value) {
			show_traits.value = true
		}
		else if(!props.expanded) {
			filter.value = ""
			highlighted_traits.value = []
		}
		setTimeout(() => held.value = false, 500)
	}

	function toggle_info() {
		show_info.value = !show_info.value
	}

	watch(() => props.traitset?.traits, (newTraits, oldTraits) => {
		// first compare newTraits with traits, check by id
		if(newTraits && JSON.stringify(newTraits?.map(t => t.id).sort()) != JSON.stringify(traits.value.map(t => t.id).sort())) {
			traits.value = newTraits
		}
	})


	const { entity, retrieve_small_entity } = useEntity(undefined, props.entity_id)
	if(player.is_player) retrieve_small_entity()



	const { location, retrieve_parents } = useLocation(undefined, props.location_key)


	// TRAIT ADDING
	const {
		traits,
		retrieve_potential_traits
	} = useTraitList(
		undefined,
		props.traitset_id,
		props.entity_id,
		true
	)

	const adding_trait: Ref<boolean> = ref(false)
	const search_potential_traits_visible = ref(false)
	const trait_search: Ref<string> = ref("")
	const add_multiple_traits = ref(false)
	const highlighted_potential_trait = ref<TraitType|undefined>()
	
	function toggle_add_trait() {
		retrieve_default_settings()
		if(adding_trait.value) {
			adding_trait.value = false
			trait_search.value = ""
			add_multiple_traits.value = false
		}
		else {
			retrieve_potential_traits('network-only')
			emit('reset_scroll')
			retrieve_all_traits()
			retrieve_parents()
			adding_trait.value = true
		}
	}

	const potential_traits: Ref<TraitType[]> = computed(() => {
		return traits.value.filter(t => (
			traitset.value.duplicates ?
				true :
				!traitset.value.traits?.map(x => x.id).includes(t.id)
			) && t.name.toLowerCase().includes(trait_search.value.toLowerCase()))
	})

	function randomize_potential_trait() {
		let trait_list = []
		for(const potential_trait of potential_traits.value) {
			if(potential_trait.randomWeight) {
				for(let i = 0; i < potential_trait.randomWeight; i++) {
					trait_list.push(potential_trait)
				}
			}
		}
		highlighted_potential_trait.value = trait_list[Math.floor(Math.random() * trait_list.length)]
	}

	async function assign_trait_to_entity(trait: TraitType) {
		let new_trait: TraitType|null|undefined = null
		if(
			props.entity_id
			&& props.entity_id != 'placeholder'
		) {
			console.log("assigning trait: " + trait.id + " to entity: " + props.entity_id)
			set_entity(props.entity_id)
			if(!props.relationship) {
				if(location.value.parents && location.value.parents?.length > 2 && trait.locationRestricted) {
					// assign trait restricted to location
					new_trait = await assign_trait(trait.id, location.value.parents?.slice(-2, -1)[0].id, { knownTo: player.the_entity ? [player.the_entity?.id] : undefined })
				}
				else {
					// assign trait to entity
					new_trait = await assign_trait(trait.id, undefined, { knownTo: player.the_entity ? [player.the_entity?.id] : undefined })
				}
			}
			else {
				// assign trait to relationship
				new_trait = await assign_trait(trait.id, undefined, { knownTo: player.the_entity ? [player.the_entity?.id] : undefined })
			}
			await retrieve_traitset('network-only')
			show_traits.value = true
		}
		else {
			console.error("Can't assign trait to entity: " + props.entity_id)
		}

		if(!add_multiple_traits.value) {
			adding_trait.value = false
			trait_search.value = ""
			setTimeout(() => {
				if(new_trait) {
					scroll_to_trait(new_trait)
				}
			}, 200)
		}
	}

	watch(() => player.location_update_counter, () => {
		if(props.location) {
			retrieve_traitset('network-only')
		}
	})

	watch(() => player.the_entity?.traitsets, (newTraitsets, oldTraitsets) => {
		if(newTraitsets && player.the_entity?.id == props.entity_id) {
			const new_traits = newTraitsets.filter(ts => ts.id == traitset.value.id)[0].traits
			if(new_traits && JSON.stringify(new_traits?.map(t => t.id).sort()) != JSON.stringify(traitset.value.traits?.map(t => t.id).sort())) {
				console.log("updating traitset: " + traitset.value.id)
				retrieve_traitset('network-only')
			}
		}
	})

	const show_unavailable_traits = ref(false)

	async function add_trait() {
		console.log('adding trait: ' + trait_search.value)
		await create_trait(trait_search.value)
		retrieve_potential_traits('network-only')
		// trait_search.value = ""
		// setTimeout(() => retrieve_potential_traits(), 200)
	}

	const dice_in_dicepool = computed(() => {
		return traitset_dice(traitset.value.id).filter((d) => d.number_rating > 0 && d.entityId == props.entity_id)
	})

	const traits_in_dicepool: Ref<DieType[]> = computed(() => {
		return [...new Set(traitset_dice(traitset.value.id)
			.filter((d) => d.number_rating > 0 && d.entityId == props.entity_id))]
	})

	const pool_scaling_effect: Ref<number> = computed(() => {
		// take a die from traitset_dice for each unique traitsetting id and add the die.poolScaling attributes together
		return [...new Set(traitset_dice(traitset.value.id)
			.filter((d) => d.entityId == props.entity_id)
			.map((d) => d.traitsettingId))
		].reduce((acc, d) => acc + traitset_dice(traitset.value.id)
										.filter((d2) => d2.traitsettingId == d)
										.reduce((acc2, d2) => acc2 + (d2.poolScaling ?? 0), 0), 0)
	})

	const result_scaling_effect: Ref<number> = computed(() => {
		// take a die from traitset_dice for each unique traitsetting id and add the die.resultScaling attributes together
		return [...new Set(traitset_dice(traitset.value.id)
			.filter((d) => d.entityId == props.entity_id)
			.map((d) => d.traitsettingId))
		].reduce((acc, d) => acc + traitset_dice(traitset.value.id)
										.filter((d2) => d2.traitsettingId == d)
										.reduce((acc2, d2) => acc2 + (d2.resultScaling ?? 0), 0), 0)
	})

	const effect_scaling_effect: Ref<number> = computed(() => {
		// take a die from traitset_dice for each unique traitsetting id and add the die.effectScaling attributes together
		return [...new Set(traitset_dice(traitset.value.id)
			.filter((d) => d.entityId == props.entity_id)
			.map((d) => d.traitsettingId))
		].reduce((acc, d) => acc + traitset_dice(traitset.value.id)
										.filter((d2) => d2.traitsettingId == d)
										.reduce((acc2, d2) => acc2 + (d2.effectScaling ?? 0), 0), 0)
	})

	watch(() => player.perspective.location, (newLocation, oldLocation) => {
		if(player.is_gm && player.perspective_id == props.entity_id && newLocation != oldLocation) {
			// console.log("switching perspective")
			retrieve_traitset()
		}
	})

	watch(() => player.player_character.location, (newLocation, oldLocation) => {
		if(player.is_player && player.player_character.id == props.entity_id && newLocation != oldLocation) {
			retrieve_traitset()
		}
	})

	watch(() => player.editing, (newEditing) => {
		if (!newEditing) {
			highlighted_traits.value = []
			root_highlight_id.value = ''
		}
	})

	const root_highlight_id = ref<string>('')
	const highlighted_traits = ref<string[]>([])

	function highlight_traits(highlight_id: string[], root: boolean) {
		highlighted_traits.value = highlighted_traits.value.concat(highlight_id)
		if(root) {
			console.log("root highlight id: " + highlight_id[0])
			root_highlight_id.value = highlight_id[0]
			if(traitset.value.traits?.length && traitset.value.traits?.length > 0) {
				for(let i = 1; i < traitset.value.traits?.length; i++) {
					if(traitset.value.traits[i].requiredTraits?.map((t) => t.id).includes(highlight_id[0])) {
						highlight_traits([traitset.value.traits[i].id], false)
					}
				}
			}
		}
	}

	function kill_highlight_traits(highlight_id: string[], root: boolean) {
		highlighted_traits.value = highlighted_traits.value.filter((id) => !highlight_id.includes(id))
		if(root_highlight_id.value == highlight_id[0]) {
			root_highlight_id.value = ''
		}
	}

	const editing_potential_traits = ref<string[]>([])
	function toggle_editing_potential_trait(e: MouseEvent | null, trait_id: string) {
		/**
		 * Manages which traits to show as editing
		 */
		if(player.is_player) return
		if(editing_potential_traits.value.includes(trait_id)) {
			editing_potential_traits.value = editing_potential_traits.value.filter((id) => id != trait_id)
		}
		else {
			editing_potential_traits.value.push(trait_id)
		}
	}

	const got_traits_to_show = computed(() => {
		return (traitset.value.traits?.length ?? 0) > 0 && traitset.value.traits?.some((trait) => {
			return player.is_gm
				|| props.relationship
				|| (player.is_player && entity.value && entity.value.entityType == 'character')
				|| (player.is_player && trait.traitSetting && trait.traitSetting.hidden == false)
				|| (player.is_player && trait.traitSetting?.knownTo?.map((t) => t.id).includes(player.player_character.id))
		})
	})
	watch(() => props.expanded, (newExpanded) => {
		if(got_traits_to_show.value) {
			show_traits.value = newExpanded
		}

		highlighted_traits.value = []

		if(!newExpanded) {
			show_info.value = false
			adding_trait.value = false
			trait_search.value = ""
		}
	})

	// console.log(traitset.value.name + " got traits to show: " + got_traits_to_show.value)
	const show_traits: Ref<boolean> = ref(got_traits_to_show.value ? props.expanded : false)


	function toggle_traits() {
		if(!held.value) {
			if(!show_traits.value) {
				retrieve_traitset()
				emit('set_traitset', traitset.value)
			}
			else {
				show_info.value = false
				emit('unset_traitset')
			}
			show_traits.value = !show_traits.value
			highlighted_traits.value = []
			// here should emit scroll-to this traitset
		}
	}

	watch(show_traits, (newShowTraits) => {
		// only poll when showing traits
		if(!newShowTraits) {
			polling_active.value = false
		}
		else if(newShowTraits && props.polling && !polling_active.value) {
			polling_active.value = true
		}
	})
	
	/**
	 * Determines whether the traitset should be extended to allow adding traits
	 */
	const extended = computed(() => {
		return (
			(got_traits_to_show.value && props.expanded)
			|| (player.is_gm && (props.extensible || show_info || edit_mode || traitset.value.traits?.length == 0))
			|| (player.is_player && player.player_character.id == props.entity_id)
			|| (props.relationship && props.extensible)
			|| (props.location && props.extensible)
		)
	})

	const traits_to_display = computed(() => {
		if(traitset.value.traits) {
			let result = <TraitType[]>[]

			// experimental, show only traits that are highlighted
			if(highlighted_traits.value.length > 0) {
				return traitset.value.traits.filter((t) => highlighted_traits.value.includes(t.traitSettingId ?? ''))
			}

			// included trait filters
			let filtered_traits = traitset.value.traits.filter((trait) => {
				return (
					player.is_gm
					|| props.relationship
					// || (player.is_player && entity.value.entityType == 'character')
					|| (player.is_player && !trait.traitSetting?.hidden)
					|| (player.is_player && trait.traitSetting?.hidden && trait.traitSetting?.knownTo?.map((t) => t.id).includes(player.player_character.id))
					|| (player.is_player && trait.traitSetting?.hidden && trait.traitSetting.fromEntity?.id == entity.value.id)
					|| trait.traitSetting?.inherited
					|| props.tutorial
				)
				// && !(
				// 	trait.traitSetting?.hidden
				// 	&& trait.traitSetting.fromEntity?.id != entity.value.id
				// 	&& !trait.traitSetting?.knownTo?.map((t) => t.id).includes(player.player_character.id)
				// 	&& !trait.traitSetting.inherited
				// )
			})

			// console.log("filtered traits: " + JSON.stringify(filtered_traits))

			if(filtered_traits.length == 0) {
				return []
			}

			// get unique traits, by name and if it's not inheritable also statement
			// traitset.duplicates means that duplicate traits are allowed
			// old version: t.name + ((traitset.value.duplicates == false || t.traitSetting?.inheritable == true) ? '' : (t.traitSetting?.statement ?? ''))
			const unique_traits: string[] = Array.from(new Set(filtered_traits.map((t) =>
				t.name + (traitset.value.duplicates == false ? '' : (t.traitSetting?.statement ?? ''))
			)))

			if(traitset.value.name == "challenges") console.log("unique traits: " + JSON.stringify(unique_traits))

			// for each unique trait, get the highest priority trait
			unique_traits.forEach((ut) => {
				const ut_traits = filtered_traits.filter((t) => {
					return t.name + (traitset.value.duplicates == false ? '' : (t.traitSetting?.statement ?? '')) == ut
				})
				if(ut_traits.length == 0) {
					// console.log("traitset duplicates: " + traitset.value.duplicates + ", no traits found for '" + ut + "'")
					return
				}
				const highest_priority_trait = ut_traits.reduce((a, b) => (a?.traitSetting?.priority ?? -1) > (b?.traitSetting?.priority ?? -1) ? a : b)
				if(highest_priority_trait) {
					result.push(highest_priority_trait)
				}
			})

			result.push(...filtered_traits.filter(t => {
				!result.map(x => x.traitSettingId).includes(t.traitSettingId)
				&& t.traitSetting?.fromEntity?.id == props.entity_id
			}))

			// if a text filter is set, filter the traits on: name, statement, notes
			if(filter.value && result.length > 0) {
				result = result.filter((t) => {
					return (
						t.name.toLowerCase().includes(filter.value.toLowerCase())
						|| (t.traitSetting?.statement ?? '').toLowerCase().includes(filter.value.toLowerCase())
						|| (t.traitSetting?.notes ?? '').toLowerCase().includes(filter.value.toLowerCase())
					)
				})
			}

			return result
		}
		else {
			return []
		}
	})

	// the user changes location, so reflect that in the traits
	watch(() => player.the_entity?.location, (newLocation, oldLocation) => {
		if(newLocation != oldLocation) {
			retrieve_traitset('network-only')
		}
	})

	function next_sort() {
		const index = SORTING.findIndex((s) => JSON.stringify(s) === JSON.stringify(sorting.value))
		sorting.value = SORTING[SORTING.length > index + 1 ? index + 1 : 0]
		update_traitset_settings({ sorting: sorting.value.id })
		retrieve_traitset()
	}

	const trait_mode = ref<view_modes>(view_modes.Neutral)
	async function next_trait_mode(reverse: boolean = false) {
		const index = Object.values(view_modes).findIndex((s) => s === trait_mode.value)
		if(!reverse) {
			trait_mode.value = Object.values(view_modes)[Object.values(view_modes).length > index + 1 ? index + 1 : 0]
		}
		else {
			trait_mode.value = Object.values(view_modes)[index > 0 ? index - 1 : Object.values(view_modes).length - 1]
		}
		await update_traitset_settings({ traitMode: trait_mode.value })
		await retrieve_traitset_setting('network-only')
	}

	function change_limit(limit: number) {
		limiter.value += limit
		if(limiter.value >= 0) {
			update_traitset_settings({ limit: limiter.value })
		}
		else {
			limiter.value = 0
		}
	}

	function random_highlight() {
		// randomly highlight a trait
		if(highlighted_traits.value.length > 0) {
			highlighted_traits.value = []
		}
		else if(traits_to_display.value.length && traits_to_display.value.length > 0) {
			const trait = traits_to_display.value[Math.floor(Math.random() * traits_to_display.value.length)]
			if(trait.traitSettingId) {
				highlighted_traits.value = [trait.traitSettingId]
			}
		}
	}

	const score = computed(() => {
		return traits_to_display.value.reduce((acc, cur) => {
			return acc + cur.rating?.map(r => [1,2,3,5,8][r-1] ?? 0).reduce((a, b) => a + b, 0)
		}, 0) ?? 0
	})

	const edit_mode = ref(false)
	function toggle_edit_mode() {
		edit_mode.value = !edit_mode.value
		if(!edit_mode.value) {
			adding_trait.value = false
		}
	}
	
	const filter = ref('')
	const filtering = ref(false)


	const refreshing = ref(false)
	async function refresh() {
		refreshing.value = true
		await retrieve_traitset('network-only').then(() => {
			refreshing.value = false
		})
	}

	const active_trait_id = ref("")

	function scroll_to_element(element_id: string) {
		console.log("scrolling to element: " + element_id)
		const element = document.getElementById(element_id)
		if(element) {
			console.log("element found, scrolling to it")
			element.scrollIntoView({ behavior: 'smooth', block: 'center' })
		}
	}

	function scroll_to_trait(trait: TraitType) {
		console.log("scrolling to trait: " + trait.id)
		active_trait_id.value = trait.id
		nextTick(() => scroll_to_element('ts-' + trait.traitSettingId + '-' + entity.value.key))
	}
</script>

<template>
	<div class="traitset"
			:class="[
				props.active || show_traits ? 'active' : 'inactive',
				{ 'editing': player.editing },
				{ 'next': props.next },
				'ts-' + traitset.name?.replace(' ', '-').toLowerCase(),
				{ 'minimal': props.hide_title && props.expanded },
				{ 'relationships': props.relationship },
				{ 'gm': traitset.entityTypes?.includes('gm') },
				{ 'editing-traits': edit_mode },
				{ 'full': limiter > 0 && traits_in_dicepool.length >= limiter },
			]"
			:id="'ts-' + traitset.name?.replace(' ', '-').toLowerCase() + '-' + props.entity_id.substring(props.entity_id.indexOf('/') + 1)"
			v-if="(
					traits_to_display.length > 0
					|| props.visible
				)
				&& (
					player.is_gm
					|| (
						player.is_player
						&& !traitset.entityTypes?.includes('gm')
					)
				)">

		<div class="set-title" v-if="(!props.hide_title || player.editing || show_info)"
				@click="toggle_traits"
				v-touch:hold="title_longpress"
				@click.right="title_longpress"
				@contextmenu="(e) => e.preventDefault()"
				:class="{ 'extended': extended }">
			<div class="trait-count" v-if="!show_traits">
				{{ traitset.traits ? traits_to_display.length : '' }}
			</div>
			<div v-else class="button-mnml" @click.stop="toggle_info">
				<!-- <span class="icon">ℹ️</span> -->
				<img src="/img/icons/info.png" class="icon" />
			</div>
			
			<div class="title">
				<!-- <div class="big-limiter" v-if="show_traits && props.active">
					<span v-for="d of dice_in_dicepool" :key="d.id">
						{{ die_shapes[d.rating + (d.number_rating >= 0 ? '_active' : '_inactive')] }}
					</span>
					<span v-if="limiter - traits_in_dicepool.length > 0" v-for="i in limiter - traits_in_dicepool.length" :key="i">
						{{ die_shapes.default_inactive }}
					</span>
				</div> -->

				<span class="traitset-name">
					{{ (traitset.name?.toUpperCase() ?? '') }}
				</span>

				<span class="dicepool-traits" v-if="!show_traits">
					<TraitLabel v-for="t of new Set(traits_in_dicepool.map((t: DieType) => t.traitsettingId))" :key="t" :trait_setting_id="t" />
				</span>

			</div>
			<div class="limiter">
				<span class="pool-scaling" v-if="pool_scaling_effect != 0">
					{{ pool_scaling_effect < 0 ? '-' : '+' }}{{ pool_scaling_effect }}
				</span>
				<span class="result-scaling" v-if="result_scaling_effect != 0">
					{{ result_scaling_effect < 0 ? '-' : '+' }}{{ result_scaling_effect }}
				</span>
				<span class="effect-scaling" v-if="effect_scaling_effect != 0">
					{{ effect_scaling_effect < 0 ? '-' : '+' }}{{ effect_scaling_effect }}
				</span>
				<span v-if="limiter - traits_in_dicepool.length > 0" v-for="i in limiter - traits_in_dicepool.length" :key="i">
					{{ die_shapes.default_inactive }}
				</span>
				<span v-for="d of dice_in_dicepool.filter((d) => d.number_rating >= 0)" :key="d.id">
					{{ die_shapes[d.rating + (d.number_rating >= 0 ? '_active' : '_inactive')] }}
				</span>
			</div>

			<!-- <div v-else></div> -->
		</div>


		<div class="traitset-info" v-if="!props.hide_title && show_info">
			<div class="options">
				<div class="traitset-limiter">
					<div type="button" class="button-mnml change-limit limit-decrease"
						@click.stop="change_limit(-1)">
						<!-- <div class="icon">⊖</div> -->
						<img src="/img/icons/minus.png" class="icon" />
						<div class="label" v-if="!player.small_buttons">decrease limit</div>
					</div>
					<div type="button" class="button-mnml change-limit limit-increase"
						@click.stop="change_limit(1)">
						<!-- <div class="icon">⊕</div> -->
						<img src="/img/icons/plus.png" class="icon" />
						<div class="label" v-if="!player.small_buttons">increase limit</div>
					</div>
				</div>
				<div type="button" class="button-mnml edit-traits" :class="{ 'active': edit_mode }"
					@click.stop="toggle_edit_mode" v-if="show_traits">
					<div class="icon">✎</div>
					<div class="label" v-if="!player.small_buttons">{{ 'edit' + (edit_mode ? 'ing' : '') + ' ' + traitset.name }}</div>
				</div>
				<div class="traitset-filter" :class="{ 'active': filtering }" v-if="traitset.traits && traitset.traits.length > 0">
					<input type="text" class="filter" v-model="filter" placeholder="filter" v-if="filtering" />
					<div class="button-mnml" title="filter"
						@click.stop="filtering = !filtering">
						<div class="icon">{{ filtering ? '✖' : '&#x1F50D;'}}</div>
						<div class="label">{{ player.small_buttons ? '' : '\nfilter' }}</div>
					</div>
				</div>
				<div class="button-mnml" :class="{ 'active': highlighted_traits.length > 0 }"
						@click.stop="random_highlight">
						<div class="icon">🎲</div>
						<div class="label">{{ player.small_buttons ? '' : '\nrandom' }}</div>
				</div>
				<div class="button-mnml sort-button" @click.stop="next_sort">
					<div class="icon">⇅</div>
					<div class="label">{{ player.small_buttons ? '' : '\n' + sorting.text }}</div>
				</div>
				<div class="button-mnml trait-mode-button"
						@click.stop="next_trait_mode(false)"
						@click.right.stop="next_trait_mode(true)"
						@contextmenu="(e) => e.preventDefault()"
						v-if="props.entity?.entityType == 'character' || player.is_gm">
					<div class="icon">-?-</div>
					<div class="label">{{ player.small_buttons ? '' : '\n' + trait_mode }}</div>
				</div>
				<div class="button-mnml" :class="{ 'disabled': refreshing }" id="refresh-traitset"
					@click.stop="refresh">
					<div class="icon">🔄</div>
					<div class="label">{{ player.small_buttons ? '' : '\nrefresh' }}</div>
				</div>
				<!-- <input type="button" class="button add-trait-button"
					:value="adding_trait ?
						player.small_buttons ? 'x' : 'stop adding trait x' :
						player.small_buttons ? '+' : 'add ' + traitset.name + ' +'"
					@click="toggle_add_trait" /> -->
				<div class="button-mnml add-trait-button" :class="{ 'active': adding_trait }"
					@click.stop="toggle_add_trait">
					<div class="icon">{{ adding_trait ? '✖' : '+' }}</div>
					<div class="label" v-if="!player.small_buttons && !adding_trait">add {{ traitset.name }}</div>
					<div class="label" v-if="!player.small_buttons && adding_trait">stop adding trait</div>
				</div>
				<div class="button-mnml traitset-score" v-if="score" title="score">
					<div class="icon">{{ score }}</div>
					<div class="label" v-if="!player.small_buttons">score</div>
				</div>
			</div>
			<div class="gm-info" v-if="player.is_gm">{{ traitset.id }}</div>
			<div class="traitset-explainer" v-if="traitset.explainer" v-html="traitset.explainer"></div>
		</div>


		<div class="traits" v-if="show_traits == true || extended == true" :class="{ 'hidden_title': (props.hide_title && player.editing) }">

			<div class="traitset-sfxs" v-if="!props.hide_title && traitset.sfxs && traitset.sfxs.length > 0 && show_traits">
				<!-- <div class="sfx-sparkles">✨</div> -->
				<template v-for="sfx in traitset.sfxs" :key="sfx.id">
					<SFX :sfx_id="sfx.id"
						:expanded="expanded_sfx == sfx"
						@expand="expanded_sfx = sfx"
						@collapse="expanded_sfx = {} as SFXType" />
				</template>
			</div>

			<div class="entity-traits" v-if="(show_traits || extended) && !adding_trait">
				<template class="highlighted-traits" v-for="trait in traits_to_display"
						:key="trait.traitSettingId"
						v-if="highlighted_traits.length > 0">
					<Trait
						:highlighted="highlighted_traits.includes(trait.traitSettingId ?? '')"
						:trait_id="trait.id"
						:traitset_id="traitset.id"
						:trait_setting_id="trait.traitSettingId"
						:entity_id="props.entity_id"
						:highlight_root_id="root_highlight_id"
						:location_key="props.location_key"
						:traitset_limit="limiter"
						:edit_mode="edit_mode"
						:filter="filter"
						:traitset_types="traitset.entityTypes"
						:mode="view_modes.Viewing"
						@refetch="retrieve_traitset('network-only')"
						@next_traitset="limiter - dice_in_dicepool.length <= 0 ? $emit('next') : null"
						@set_highlight="highlight_traits"
						@kill_highlight="kill_highlight_traits"
						v-if="(player.is_gm
							|| props.relationship
							|| (player.is_player && entity.entityType == 'character')
							|| (player.is_player && trait.traitSetting && !trait.traitSetting.hidden)
							|| (player.is_player && trait.traitSetting?.hidden && trait.traitSetting?.knownTo?.map((t) => t.id).includes(player.player_character.id))
							|| props.tutorial)
							&& (
								(
									traits_in_dicepool.length == limiter
									&& (
										traits_in_dicepool.map((t: DieType) => t.traitsettingId).includes(trait.traitSettingId)
										|| traits_in_dicepool.map((t: DieType) => t.traitsettingId).some((id) => trait.subTraits?.some((st) => st.traitSettingId == id))
									)
								)
								|| traitset_dice(traitset.id).length < limiter
								|| limiter == 0
							)
						" />
					<!-- <div class="trait-divider"
						v-if="
							highlighted_traits.length > 0 &&
							traitset.traits?.some((t) => t.requiredTraits && t.requiredTraits.length > 0) ?
							highlighted_traits.includes(trait.id) && highlighted_traits.indexOf(trait.id) < highlighted_traits.length - 1 :
							traitset.traits && traitset.traits.indexOf(trait) < traitset.traits.length - 1
						"></div> -->
				</template>
				<template class="not-highlighted-traits" v-if="show_traits && highlighted_traits.length == 0" v-for="trait in traits_to_display"
						:key="trait.traitSettingId">
					<Trait
						class="traitset-trait"
						:id="'ts-' + trait.traitSettingId + '-' + entity.key"
						:highlighted="highlighted_traits.includes(trait.traitSettingId ?? '')"
						:trait_id="trait.id"
						:traitset_id="traitset.id"
						:trait_setting_id="trait.traitSettingId"
						:entity_id="props.entity_id"
						:entity="props.entity"
						:highlight_root_id="root_highlight_id"
						:location_key="props.location_key"
						:traitset_limit="limiter"
						:edit_mode="edit_mode"
						:filter="filter"
						:traitset_types="traitset.entityTypes"
						:mode="traitset.traitsetSetting?.traitMode ?? (edit_mode ? view_modes.Editing : player.is_player ? view_modes.Small : view_modes.Neutral)"
						@refetch="retrieve_traitset('network-only')"
						@next_traitset="limiter - dice_in_dicepool.length <= 0 ? $emit('next') : null"
						@set_highlight="highlight_traits"
						@kill_highlight="kill_highlight_traits"
						@show_trait="scroll_to_trait"
						@show_entity="(e_id) => emit('show_entity', e_id)"
						v-if="(player.is_gm
							|| props.relationship
							|| (player.is_player && entity.entityType == 'character')
							|| (player.is_player && trait.traitSetting && !trait.traitSetting.hidden)
							|| (player.is_player && trait.traitSetting?.hidden && trait.traitSetting?.knownTo?.map((t) => t.id).includes(player.player_character.id))
							|| props.tutorial)
							&& (
								(
									traits_in_dicepool.length >= limiter
									&& (
										traits_in_dicepool.map((t: DieType) => t.traitsettingId).includes(trait.traitSettingId)
										|| traits_in_dicepool.map((t: DieType) => t.traitsettingId)
											.some((traitsettingId) => trait.subTraits?.some((st) => st.traitSettingId == traitsettingId))
									)
								)
								|| traits_in_dicepool.length < limiter
								|| limiter == 0
							)
						" />
					<!-- <div class="trait-divider"
						v-if="
							highlighted_traits.length > 0 &&
							traitset.traits?.some((t) => t.requiredTraits && t.requiredTraits.length > 0) ?
							highlighted_traits.includes(trait.id) && highlighted_traits.indexOf(trait.id) < highlighted_traits.length - 1 :
							traitset.traits && traitset.traits.indexOf(trait) < traitset.traits.length - 1
						"></div> -->
				</template>
				<div class="add-trait" v-if="
							(
								(player.is_gm && show_traits && !props.hide_title)
								|| (
									player.is_player
									&& player.player_character.id == props.entity_id
									&& (props.expanded || show_traits)
								)
								|| (props.relationship && props.extensible)
								|| (props.location && props.extensible && !props.hide_title && show_traits)
								|| adding_trait
							) && (
								traits_in_dicepool.length < limiter
								|| traits_in_dicepool.length == 0
							)
						">
					<input type="button" class="button add-trait-button"
						:value="adding_trait ?
							player.small_buttons ? 'x' : 'stop adding trait x' :
							player.small_buttons ? '+' : 'add ' + traitset.name + ' +'"
						@click="toggle_add_trait" />
				</div>
			</div>

			<div class="add_trait" v-if="adding_trait">


				<div v-if="potential_traits.length == 0" class="no-results">no available traits to add</div>

				<div class="controls">
				
					<div class="button-mnml add-multiple-toggle" @click="add_multiple_traits = !add_multiple_traits">
						<div class="icon">{{ add_multiple_traits ? '☑' : '⭕' }}</div>
						<div class="label">adding {{ add_multiple_traits ? 'multiple' : 'single' }}</div>
					</div>
					<div class="button-mnml randomize" @click="randomize_potential_trait">
						<div class="icon">🎲</div>
						<div class="label">random trait</div>
					</div>
					<div class="trait-search" v-if="player.is_gm || potential_traits.length >= 0">
						<input class="trait-search-query" type="text" placeholder="find trait"
							v-model="trait_search" autocomplete="off" />
						<input type="button" class="button create-trait-button"
							:value="'create ' + trait_search"
							v-if="trait_search.length > 0
								&& traits.filter(
									t => t.name.toLowerCase() == trait_search.toLowerCase()
								).length == 0
								&& player.is_gm"
							@click="add_trait" />
					</div>
					<!-- <div class="search-potential-trait-toggle" :class="search_potential_traits_visible ? 'active' : 'inactive'" v-if="potential_traits.length > 0">
						<div class="button" @click="search_potential_traits_visible = true" v-if="!search_potential_traits_visible">search for trait</div>
						<div class="button" @click="search_potential_traits_visible = false" v-else>x</div>
					</div> -->

					<input type="button" class="button add-trait-button"
						:value="adding_trait ?
							player.small_buttons ? 'x' : 'stop adding trait x' :
							player.small_buttons ? '+' : 'add ' + traitset.name + ' +'"
						@click="toggle_add_trait" />
				</div>
				<div class="trait-list">
					<template v-for="trait in potential_traits" :key="trait.id" v-if="potential_traits.length > 0">
						<div class="button potential-trait"
								:class="[
									trait.defaultTraitSetting?.rating && trait.defaultTraitSetting?.rating?.length > 0 ?
										trait.defaultTraitSetting?.rating.map((r) => r.rating)[0] : 'dn',
									trait.defaultTraitSetting?.rating && trait.defaultTraitSetting?.rating.map((r) => r.number_rating)[0] > 0 ?
										'positive' : 'negative',
									{ 'highlighted': highlighted_potential_trait?.id == trait.id }
								]"
								@click="assign_trait_to_entity(trait)"
								@click.right.stop="(e) => toggle_editing_potential_trait(e, trait.id)"
								v-touch:hold="() => toggle_editing_potential_trait(null, trait.id)"
								@contextmenu="(e) => e.preventDefault()">
							<div class="trait-description">
								<div class="trait-name">{{ trait.name }}</div>
								<div class="trait-explanation"
									v-html="marked(trait.explanation ?? '')"></div>
							</div>
							<span class="trait-rating">
								{{ trait.defaultTraitSetting?.rating ? trait.defaultTraitSetting?.rating.map((r) => r.active)[0] : '' }}
							</span>
						</div>
						<TraitEdit
							:trait_id="trait.id"
							:trait_name="trait.name"
							:expanded="true"
							@refetch_traits="retrieve_potential_traits('network-only')"
							v-if="player.is_gm && editing_potential_traits.includes(trait.id)" />
					</template>
				</div>

				<div class="unavailable-traits-title" @click="show_unavailable_traits = !show_unavailable_traits">
					{{ show_unavailable_traits ? 'hide unavailable traits' : 'show unavailable traits' }}
				</div>
				<div class="trait-list" v-if="show_unavailable_traits">
					<template v-for="trait in all_traits.sort((t1, t2) => t1.name.localeCompare(t2.name)).filter(t => t.name.toLowerCase().includes(trait_search.toLowerCase()))" :key="trait.id">
						<div class="button excluded-trait" :class="trait.defaultTraitSetting?.rating ? trait.defaultTraitSetting?.rating.map((r) => r.rating)[0] : 'dn'"
								v-if="
									!potential_traits.map(t => t.id).includes(trait.id)
								"
								@click="player.is_gm ? assign_trait_to_entity(trait) : null"
								@click.right.stop="(e) => toggle_editing_potential_trait(e, trait.id)"
								@contextmenu="(e) => e.preventDefault()">
							<div class="trait-description">
								<div class="trait-name">{{ trait.name }}</div>
								<div class="trait-explanation"
									v-html="marked(trait.explanation ?? '')"></div>
							</div>
							<span class="trait-rating">
								{{ trait.defaultTraitSetting?.rating ? trait.defaultTraitSetting?.rating.map((r) => r.active)[0] : '' }}
							</span>
						</div>
						<TraitEdit :trait_id="trait.id" :trait_name="trait.name" :expanded="true" v-if="editing_potential_traits.includes(trait.id)" />
					</template>
				</div>
			</div>
		</div>

	</div>
</template>

<style scoped>
	.traitset {
		&.active, &.next {
			width: 100%;
		}
		.set-title {
			position: sticky;
			top: 0;
			text-align: center;
			font-size: 1.2em;
			cursor: pointer;
			/* padding: .4em 0; */
			justify-content: space-between;
			display: flex;
			z-index: 2;
			gap: 1em;
			max-width: 100vw;
			overflow-x: hidden;
			.trait-count {
				width: 3em;
				text-align: right;
				/* padding-right: 1em; */
			}
			.title {
				position: relative;
				display: flex;
				align-items: center;
				flex-grow: 1;
				.dicepool-traits {
					height: 100%;
					flex-grow: 1;
					display: flex;
					gap: .4em;
					flex-wrap: wrap;
					justify-content: center;
					align-items: center;
				}
			}
			.limiter {
				/* min-width: 4em; */
				/* padding-right: 1em; */
				text-align: right;
				flex-grow: 1;
				display: flex;
				justify-content: space-around;
			}
			.button-mnml {
				/* padding: 0 1em; */
				&.change-limit {
					background-color: var(--color-highlight);
					color: var(--color-highlight-text);
				}
				&.disabled {
					background-color: var(--color-disabled);
					color: var(--color-disabled-text);
				}
			}
			.score {
				width: 20%;
				font-size: small;
			}
		}
		.traitset-info {
			border-bottom: 1px solid var(--color-border);
			padding: .4em 2em;
			min-height: 3em;
			overflow: hidden;
			.traitset-explainer {
				display: inline;
			}
			.options {
				display: flex;
				justify-content: space-evenly;
				flex-wrap: wrap;
				max-width: 100%;
				> div {
					height: 4em;
					/* border: 1px solid var(--color-border); */
				}
				.traitset-filter {
					display: flex;
					&.active {
						background-color: var(--color-highlight-mute);
						color: var(--color-highlight-text);
					}
				}
				.traitset-limiter {
					display: flex;
					gap: .4em;
				}
				.traitset-score {
					font-size: 1.2em;
					padding: .4em 1em;
				}
			}
		}
		.traitset-sfxs {
			position: relative;
			padding-left: 1.5em;
			border-bottom: 1px solid var(--color-border);
			background-color: var(--color-background-mute);
			display: flex;
			flex-wrap: wrap;
			font-size: 0.8em;
			.sfx-sparkles {
				position: absolute;
				left: .4em;
				top: .4em;
			}
		}
		.traits-transition-enter-active,
		.traits-transition-leave-active {
			transition: max-height 0s linear;
		}
		.traits-transition-enter-from,
		.traits-transition-leave-to {
			max-height: 0;
		}
		.traits-transition-enter-to,
		.traits-transition-leave-from {
			max-height: 100vh;
		}
		.traits {
			/* display: block;
			height: auto;
			overflow-y: auto; */
			.add-trait {
				flex-grow: 1 0;
				display: flex;
				align-items: end;
				.add-trait-button {
					max-height: 2em;
					background-color: var(--color-background-mute);
				}
			}
		}
		.traits.hidden_title .explainer {
			padding: 0 2em 0 2em;
		}
		.add_trait {
			text-align: center;
			padding: 1em;
			.controls {
				display: flex;
				justify-content: space-between;
				align-items: start;
				.trait-search {
					flex: 1;
					display: flex;
					justify-content: center;
					.trait-search-query {
						font-size: 1.2em;
						height: 2em;
						border-radius: 10px;
						padding: 0 1em;
					}
					.create-trait-button {
						background-color: var(--color-highlight);
						color: var(--color-highlight-text);
						margin: 0;
						margin-left: .2em;
						border-radius: 0 10px 10px 0;
						height: 2em;
					}
				}
				.add-trait-button {
					
				}
			}
			.trait-search.creatable {
				.trait-search-query {
					border-radius: 10px 0 0 10px;
				}
			}
			.trait-list {
				display: flex;
				flex-wrap: wrap;
				justify-content: center;
				/* align-items: center; */
				gap: .4em;
				padding: 1em;
				width: 100%;
				.search-potential-trait-toggle {
					&.inactive {
						.button {
							background-color: var(--color-highlight);
							color: var(--color-highlight-text);
						}
					}
				}
				.potential-trait, .excluded-trait {
					/* flex-grow: 1; */
					/* max-width: 50%; */
					min-width: 20%;
					align-items: center;
					display: flex;
					border-radius: 10px;
					padding: 1px;
					cursor: pointer;
					.trait-rating {
						width: 2em;
						vertical-align: middle;
						padding: 0 .1em;
						font-size: .8em;
						text-shadow: none;
					}
					.trait-description {
						text-align: left;
						flex-grow: 1;
						border-radius: 10px;
						padding: 0 .4em;
						background-color: var(--color-background-soft);
						color: var(--color-text);
						.trait-name {
							
						}
						.trait-explanation {
							font-size: .8em;
						}
					}
					&.highlighted .trait-description {
						background-color: var(--color-highlight);
						color: var(--color-highlight-text);
					}
				}
				.potential-trait.dn {
					background-color: var(--color-border);
				}
				.potential-trait.d4.positive {
					background-color: var(--color-positive-die-4);
					color: var(--color-positive-die-4-text);
				}
				.potential-trait.d6.positive {
					background-color: var(--color-positive-die-6);
					color: var(--color-positive-die-6-text);
				}
				.potential-trait.d8.positive {
					background-color: var(--color-positive-die-8);
					color: var(--color-positive-die-8-text);
				}
				.potential-trait.d10.positive {
					background-color: var(--color-positive-die-10);
					color: var(--color-positive-die-10-text);
				}
				.potential-trait.d12.positive {
					background-color: var(--color-positive-die-12);
					color: var(--color-positive-die-12-text);
				}
				.potential-trait.d4.negative {
					background-color: var(--color-negative-die-4);
					color: var(--color-negative-die-4-text);
				}
				.potential-trait.d6.negative {
					background-color: var(--color-negative-die-6);
					color: var(--color-negative-die-6-text);
				}
				.potential-trait.d8.negative {
					background-color: var(--color-negative-die-8);
					color: var(--color-negative-die-8-text);
				}
				.potential-trait.d10.negative {
					background-color: var(--color-negative-die-10);
					color: var(--color-negative-die-10-text);
				}
				.potential-trait.d12.negative {
					background-color: var(--color-negative-die-12);
					color: var(--color-negative-die-12-text);
				}
				.potential-trait.dis {
					border-color: var(--color-text);
				}
				.excluded-trait {
					background-color: var(--color-background-soft);
					color: var(--color-text);
					.trait-name {
						background-color: var(--color-background);
					}
				}
			}
		}
		.trait-divider {
			background-color: var(--color-border);
			height: 1px;
			width: 100%;
		}
		.edit-traits.active {
			font-weight: bold;
		}
	}
	.traitset.active {
		.set-title {
			padding: 0;
			justify-content: space-between;
			.title {
				flex-direction: column;
				align-content: end;
				justify-content: center;
				font-weight: bold;
				.big-limiter {
					line-height: 1em;
					font-size: 2em;
					text-align: center;
				}
				.traitset-name {
					vertical-align: text-bottom;
				}
			}
		}
	}
	.traitset.inactive {
		.set-title {
			.title {
				width: 60%;
				font-size: .8em;
			}
		}
	}
</style>

<style>
	.touch {
		.traitset {
			.entity-traits {
				flex-direction: column;
				overflow-x: hidden;
				overflow-y: auto;
				scroll-snap-type: y mandatory;
				scroll-behavior: smooth;
			}
			.add_trait {
				.controls {
					/* width: 100%; */
					/* overflow: hidden;
					.add-multiple-toggle, .trait-search, .add-trait-button {
						flex-grow: 1;
					} */
					.trait-search, .trait-search-query {
						min-width: 0;
					}
				}
			}
			&.active {
				max-height: 90%;
			}
		}
	}
	.kbm {
		.traitset {
			.set-title {
				position: sticky;
				z-index: 2;
				top: 0;
			}
			.entity-traits {
				flex-direction: column;
				align-items: center;
				overflow-x: hidden;
				overflow-y: auto;
				.traitset-trait {
					width: 100%;
				}
				.add-trait {
					width: 100%;
					justify-content: end;
				}
			}
		}
	}
	.touch.dark {
		.traitset .entity-traits {
			align-items: center;
		}
	}
	.dark {
		.traitset {
			scroll-snap-align: center;
			scroll-snap-stop: always;
			display: flex;
			flex-direction: column;
			flex-grow: 1;
			.set-title {
				letter-spacing: .1em;
				&.extended {
					background-color: var(--color-background-mute);
					/* color: var(--color-); */
				}
				.limiter {
					padding-right: .6em;
					align-items: center;
					span {
						line-height: 1.4em;
					}
				}
			}
			.traits {
				height: 100%;
				overflow: hidden;
				display: flex;
				flex-direction: column;
				/* align-items: center; */
				background-color: var(--color-background-mute);
				box-shadow: inset 0 0 30px var(--color-background-mute);
				.traitset-info {
					text-shadow: var(--text-shadow);
					.traitset-score {
						border: 1px solid var(--color-border);
						box-shadow: inset 0 0 10px var(--color-background-mute);
					}
				}
				.traitset-sfxs {
					backdrop-filter: blur(5px);
					text-shadow: var(--color-background) 0px 0px 4px,
						var(--color-background) 0px 0px 8px,
						var(--color-background) 0px 0px 16px,
						var(--color-background) 0px 0px 4px;
				}
				.entity-traits {
					/* box-shadow: inset 0 0 10px var(--color-highlight-mute); */
					display: flex;
					padding: .2em;
					/* gap: 1.4em; */
					/* background-color: var(--color-background-mute); */
					.add-trait {
						justify-content: end;
						scroll-snap-align: end;
					}
				}
				.add_trait {
					height: 100%;
					display: flex;
					flex-direction: column;
					overflow: hidden;
					.trait-list {
						flex-grow: 1;
						display: flex;
						flex-direction: column;
						overflow-x: auto;
						overflow-y: hidden;
						scroll-snap-type: x mandatory;
						.potential-trait, .excluded-trait {
							scroll-snap-align: center;
							/* max-width: 40%; */
						}
					}
				}
			}
			.trait-divider {
				display: none;
			}
			&.active {
				.set-title {
					background-color: var(--color-background);
					text-shadow: none;
					.title {
						font-size: 1.4em;
					}
				}
			}
			&.inactive {
				.set-title {
					justify-content: space-between;
					.trait-count {
						width: 60px;
					}
					.title {
						gap: 1em;
					}
				}
			}
			&.inactive.full {
				box-shadow: 0 0 10px var(--color-highlight);
				.trait-count,
				.title .traitset-name {
					color: var(--color-background);
					text-shadow: 0 0 4px var(--color-highlight);
				}
			}
			&.inactive.next {
				border-top: 1px solid var(--color-border);
			}
			&.editing-traits {
				.entity-traits {
					background-color: var(--color-editing-mute);
				}
			}
		}
		&.has-image {
			/* .traitset.active .set-title {
				background-color: var(--color-background-mute);
				color: var(--color-text);
			} */
			.traitset.active .traits {
				/* box-shadow: inset 0 0 20px var(--color-background-mute); */
			}
		}
		&.editing {
			.traitset.active .set-title {
				background-color: var(--color-editing-mute);
				color: var(--color-editing-text);
			}
			.traitset.active .traits {
				box-shadow: inset 0 0 10px var(--color-editing-mute);
				border: 1px solid var(--color-editing-mute);
			}
		}
	}
	.light {
		.traitset {
			.set-title {
				background-color: var(--color-background);
				/* color: var(--color-background); */
				.trait-count {
					display: flex;
					justify-content: end;
					align-items: center;
				}
				.traitset-name {
					font-size: 1.4em;
					padding: .4em 0;
					line-height: 0.4em;
				}
				.edit-traits.active {
					background-color: var(--color-editing);
					color: var(--color-editing-text);
				}
			}
			.entity-traits {
				background-color: var(--color-background);
				display: flex;
				flex-direction: column;
				.add-trait {
					width: 100%;
					/* background-color: var(--color-background); */
					color: var(--color-text);
					/* justify-content: center; */
				}
			}
			&.active {
				border-top: 1px solid var(--color-border);
				border-bottom: 1px solid var(--color-border);
				.set-title {
					/* background-color: var(--color-background); */
					border-bottom: 3px double var(--color-text);
				}
				.minimal {
					border: none;
				}
			}
			&.inactive {
				.next {
					background-color: var(--color-background);
					border-top: 1px solid var(--color-border);
				}
			}
			&.gm .set-title {
				background-color: var(--color-highlight-mute);
			}
			&.ts-complications .set-title {
				background-color: var(--color-hitch-mute);
			}
			&.editing-traits {
				.entity-traits {
					/* background-color: var(--color-editing); */
					background-image: repeating-linear-gradient(
						45deg,
						var(--color-editing-mute) 0,
						var(--color-editing-mute) 0.2em,
						var(--color-background) 0.2em,
						var(--color-background) 0.4em
					);
					padding: 1em;
					gap: 1em;
				}
			}
		}
	}
	.triptych {
		.traitset.inactive.next {
			position: sticky;
			bottom: 0;
			z-index: 1;
		}
	}
	.landscape {
		.traitset.inactive.next {
			position: sticky;
			bottom: 0;
		}
	}
</style>
