<script setup lang="ts">
	import _ from 'lodash'
	import { marked } from 'marked'

	import { ref, computed, watch, onUnmounted } from 'vue'
	import type { Ref } from 'vue'

	import Trait from '@/components/Trait.vue'
	import SFX from '@/components/SFX.vue'
	import TraitEdit from '@/components/TraitEdit.vue'
	import TraitLabel from '@/components/TraitLabel.vue'
	import { useTraitset, SORTING } from '@/composables/Traitset'
	import { useTraitList } from '@/composables/TraitList'
	import { useLocation } from '@/composables/Location'
	import { useEntity } from '@/composables/Entity'
	import { die_shapes } from '@/composables/Die'
	import type { SFX as SFXType, Trait as TraitType, Die as DieType } from '@/interfaces/Types'

	import { usePlayer } from '@/stores/Player'
	import { useDicepool } from '@/composables/Dicepool'

	const props = defineProps<{
		traitset_id: string,
		entity_id: string,
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
		polling?: boolean
	}>()

	const emit = defineEmits(['next', 'set_traitset', 'unset_traitset'])

	const player = usePlayer()
	const { traitset_dice } = useDicepool()

	const {
		traitset,
		retrieve_traitset,
		retrieve_default_settings,
		create_trait,
		assign_trait,
		assign_locationrestricted_trait,
		set_entity,
		sorting,
		update_traitset_settings
	} = useTraitset(
		undefined,
		props.traitset_id,
		props.relation_id ?? props.entity_id,
		SORTING[0].id
	)

	const {
		traits,
		retrieve_potential_traits
	} = useTraitList(
		undefined,
		props.traitset_id,
		props.entity_id,
		true
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

	retrieve_traitset()
	retrieve_default_settings()

	const limiter: Ref<number> = ref(props.limit ?? traitset.value.limit ?? 1)

	const expanded_sfx: Ref<SFXType> = ref({} as SFXType)

	const adding_trait: Ref<boolean> = ref(false)
	const trait_search: Ref<string> = ref("")

	const show_traits: Ref<boolean> = ref(props.expanded || false)
	watch(() => props.expanded, (newExpanded) => {
		show_traits.value = newExpanded
		highlighted_traits.value = []
	})
	watch(show_traits, (newShowTraits) => {
		// only poll when showing traits
		if(!newShowTraits) {
			polling_active.value = false
		}
		else if(newShowTraits && props.polling && !polling_active.value) {
			polling_active.value = true
		}
	})

	const held = ref(false)

	function toggle_traits() {
		if(!held.value) {
			if(!show_traits.value) {
				retrieve_traitset()
				emit('set_traitset')
			}
			else {
				show_info.value = false
				emit('unset_traitset')
			}
			show_traits.value = !show_traits.value
			highlighted_traits.value = []
		}
	}

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

	watch(() => props.expanded, (newExpanded) => {
		if(!newExpanded) {
			show_info.value = false
			adding_trait.value = false
			trait_search.value = ""
		}
	})



	const { entity, retrieve_small_entity } = useEntity(undefined, props.entity_id)
	if(player.is_player) retrieve_small_entity()



	const { location, retrieve_parents } = useLocation(undefined, props.location_key)

	function assign_trait_to_entity(trait: TraitType) {
		if(
			props.entity_id
			&& props.entity_id != 'placeholder'
		) {
			console.log("assigning trait: " + trait.id + " to entity: " + props.entity_id)
			set_entity(props.entity_id)
			if(!props.relationship) {
				if(location.value.parents && location.value.parents?.length > 2 && trait.locationRestricted) {
					assign_trait(trait.id, location.value.parents?.slice(-2, -1)[0].id, { knownTo: player.the_entity ? [player.the_entity?.id] : undefined })
				}
				else {
					assign_trait(trait.id, undefined, { knownTo: player.the_entity ? [player.the_entity?.id] : undefined })
				}
			}
			else {
				assign_trait(trait.id, undefined, { knownTo: player.the_entity ? [player.the_entity?.id] : undefined })
			}
		}
		else {
			console.error("Can't assign trait to entity: " + props.entity_id)
		}
		if(player.is_player) {
			adding_trait.value = false
		}
		trait_search.value = ""
		setTimeout(() => retrieve_potential_traits(), 200)
		setTimeout(() => retrieve_traitset(), 200)
	}

	function toggle_add_trait() {
		retrieve_default_settings()
		if(adding_trait.value) {
			adding_trait.value = false
			trait_search.value = ""
		}
		else {
			retrieve_potential_traits()
			retrieve_all_traits()
			retrieve_parents()
			adding_trait.value = true
		}
	}

	const show_unavailable_traits = ref(player.is_gm)

	function add_trait() {
		console.log('adding trait: ' + trait_search.value)
		create_trait(trait_search.value)
		trait_search.value = ""
		setTimeout(() => retrieve_potential_traits(), 200)
	}

	const dice_in_dicepool = computed(() => {
		return traitset_dice(traitset.value.id).filter((d) => d.entityId == props.entity_id)
	})

	const traits_in_dicepool: Ref<DieType[]> = computed(() => {
		return [...new Set(traitset_dice(traitset.value.id)
			.filter((d) => d.entityId == props.entity_id))]
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
	function toggle_editing_potential_trait(e: MouseEvent, trait_id: string) {
		e.stopPropagation()
		if(player.is_player) return
		if(editing_potential_traits.value.includes(trait_id)) {
			editing_potential_traits.value = editing_potential_traits.value.filter((id) => id != trait_id)
		}
		else {
			editing_potential_traits.value.push(trait_id)
		}
	}

	const polling_active = ref(props.polling ?? false)
	
	function polling() {
		console.log("polling traitset " + traitset.value.name + " for entity " + props.entity_id)
		if(polling_active.value) {
			retrieve_traitset()
			setTimeout(polling, 15000)
		}
	}

	polling_active.value ? polling() : null

	onUnmounted(() => {
		polling_active.value = false
	})

	function next_sort() {
		const index = SORTING.findIndex((s) => JSON.stringify(s) === JSON.stringify(sorting.value))
		sorting.value = SORTING[SORTING.length > index + 1 ? index + 1 : 0]
		retrieve_traitset()
	}

	const got_traits_to_show = computed(() => {
		return traitset.value.traits?.some((trait) => {
			return player.is_gm
				|| props.relationship
				|| (player.is_player && entity.value && entity.value.entityType == 'character')
				|| (player.is_player && trait.traitSetting && trait.traitSetting.hidden == false)
				|| (player.is_player && trait.traitSetting?.knownTo?.map((t) => t.id).includes(player.player_character.id))
		})
	})

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
		if(traitset.value.traits?.length && traitset.value.traits?.length > 0) {
			const trait = traitset.value.traits[Math.floor(Math.random() * traitset.value.traits.length)]
			if(trait.traitSettingId) {
				highlighted_traits.value = [trait.traitSettingId]
			}
		}
	}

	const score = computed(() => {
		return traitset.value.traits?.reduce((acc, cur) => {
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
	const potential_traits = computed(() => {
		return traits.value.filter(t => (
			traitset.value.duplicates ?
				true :
				!traitset.value.traits.map(x => x.id).includes(t.id)
			) && t.name.toLowerCase().includes(trait_search.value.toLowerCase()))
	})
	const search_potential_traits_visible = ref(false)
	const filter = ref('')
</script>

<template>
	<div class="traitset"
			:class="[
				props.active && show_traits ? 'active' : 'inactive',
				{ 'editing': player.editing },
				{ 'next': props.next },
				'ts-' + traitset.name?.replace(' ', '-').toLowerCase(),
				{ 'minimal': props.hide_title && props.expanded },
				{ 'relationships': props.relationship },
				{ 'gm': traitset.entityTypes?.includes('gm') },
				{ 'editing-traits': edit_mode },
				{ 'full': limiter > 0 && traits_in_dicepool.length == limiter },
			]"
			v-if="(traitset.traits && traitset.traits.length > 0) || props.visible">

		<div class="set-title" v-if="(!props.hide_title || player.editing || show_info)"
				@click="toggle_traits"
				v-touch:hold="title_longpress"
				@click.right="title_longpress"
				@contextmenu="(e) => e.preventDefault()">
			<input type="button" class="button-mnml change-limit limit-decrease"
				:value="player.small_buttons ? '⊖' : '⊖\ndecrease limit'"
				@click.stop="change_limit(-1)" v-if="show_info" />
			<div class="trait-count" v-else-if="!show_traits">
				{{ traitset.traits ? traitset.traits.length : '' }}
			</div>
			<div v-else></div>

			<input type="button" class="button-mnml edit-traits" :class="{ 'active': edit_mode }"
				:value="player.small_buttons ? '✎' : '✎\nedit' + (edit_mode ? 'ing' : '') + ' traits'"
				@click.stop="toggle_edit_mode" v-if="show_traits && !show_info" />
				
			<div class="title">
				<div class="big-limiter" v-if="show_traits && props.active">
					<span v-for="d of dice_in_dicepool" :key="d.id">
						{{ die_shapes[d.rating + (d.number_rating >= 0 ? '_active' : '_inactive')] }}
					</span>
					<span v-if="limiter - traits_in_dicepool.length > 0" v-for="i in limiter - traits_in_dicepool.length" :key="i">
						{{ die_shapes.default_inactive }}
					</span>
				</div>

				<span class="traitset-name header">
					{{ (traitset.name?.toUpperCase() ?? '') }}
				</span>

				<span class="dicepool-traits" v-if="!show_traits">
					<TraitLabel v-for="t of new Set(traits_in_dicepool.map((t: DieType) => t.traitsettingId))" :key="t" :trait_setting_id="t" />
				</span>

			</div>
			<div class="limiter" v-if="!show_traits || !props.active">
				<span v-if="limiter - traits_in_dicepool.length > 0" v-for="i in limiter - traits_in_dicepool.length" :key="i">
					{{ die_shapes.default_inactive }}
				</span>
				<span v-for="d of dice_in_dicepool.filter((d) => d.number_rating >= 0)" :key="d.id">
					{{ die_shapes[d.rating + (d.number_rating >= 0 ? '_active' : '_inactive')] }}
				</span>
			</div>

			<input type="button" class="button-mnml change-limit limit-increase"
				:value="player.small_buttons ? '⊕' : '⊕\nincrease limit'"
				@click.stop="change_limit(1)" v-if="show_info" />
			<div v-else></div>
		</div>

		<!-- <Transition name="traits-transition"> -->
			<div class="traits" v-if="show_traits" :class="{ 'hidden_title': (props.hide_title && player.editing) }">

				<div class="traitset-info" v-if="!props.hide_title && show_info && (score || traitset.explainer)">
					<div class="traitset-score" v-if="score" title="score">
						{{ score }}
					</div>
					<div class="gm-info" v-if="player.is_gm">{{ traitset.id }}</div>
					<div class="traitset-explainer" v-if="traitset.explainer" v-html="traitset.explainer"></div>
					<div class="options">
						<input type="text" class="filter" v-model="filter" placeholder="filter" />
						<input type="button" class="button" value="filter"
							@click.stop="" />
						<input type="button" class="button" value="random"
							@click.stop="random_highlight" />
						<input type="button" class="button" :value="sorting.text"
							@click.stop="next_sort" />
					</div>
				</div>
				<div class="traitset-sfxs" v-if="!props.hide_title && traitset.sfxs && traitset.sfxs.length > 0">
					<div class="sfx-sparkles">✨</div>
					<template v-for="sfx in traitset.sfxs" :key="sfx.id">
						<SFX :sfx_id="sfx.id"
							@expand="expanded_sfx = sfx"
							@collapse="expanded_sfx = {} as SFXType"
							v-if="expanded_sfx.id ? sfx.id == expanded_sfx.id : true" />
					</template>
				</div>

				<div class="entity-traits" v-if="got_traits_to_show
						|| ((props.extensible || show_info || edit_mode || traitset.traits?.length == 0) && player.is_gm)
						|| (player.is_player && player.player_character.id == props.entity_id)
						|| (props.relationship && props.extensible)
						|| (props.location && props.extensible)">
					<template v-for="trait in traitset.traits?.filter(t => highlighted_traits.includes(t.traitSettingId))"
							:key="trait.traitSettingId">
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
							@refetch="retrieve_traitset"
							@next_traitset="limiter - dice_in_dicepool.length == 0 ? $emit('next') : null"
							@set_highlight="highlight_traits"
							@kill_highlight="kill_highlight_traits"
							v-if="(player.is_gm
								|| props.relationship
								|| (player.is_player && entity.entityType == 'character')
								|| (player.is_player && trait.traitSetting && trait.traitSetting.hidden == false)
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
						<div class="trait-divider"
							v-if="
								highlighted_traits.length > 0 &&
								traitset.traits?.some((t) => t.requiredTraits && t.requiredTraits.length > 0) ?
								highlighted_traits.includes(trait.id) && highlighted_traits.indexOf(trait.id) < highlighted_traits.length - 1 :
								traitset.traits && traitset.traits.indexOf(trait) < traitset.traits.length - 1
							"></div>
					</template>
					<template v-for="trait in traitset.traits?.filter(t => !highlighted_traits.includes(t.traitSettingId))"
							:key="trait.traitSettingId">
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
							@refetch="retrieve_traitset"
							@next_traitset="limiter - dice_in_dicepool.length == 0 ? $emit('next') : null"
							@set_highlight="highlight_traits"
							@kill_highlight="kill_highlight_traits"
							v-if="(player.is_gm
								|| props.relationship
								|| (player.is_player && entity.entityType == 'character')
								|| (player.is_player && trait.traitSetting && trait.traitSetting.hidden == false)
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
						<div class="trait-divider"
							v-if="
								highlighted_traits.length > 0 &&
								traitset.traits?.some((t) => t.requiredTraits && t.requiredTraits.length > 0) ?
								highlighted_traits.includes(trait.id) && highlighted_traits.indexOf(trait.id) < highlighted_traits.length - 1 :
								traitset.traits && traitset.traits.indexOf(trait) < traitset.traits.length - 1
							"></div>
					</template>
					<input type="button" class="button add-trait-button"
						v-if="
							player.is_gm
							|| (
								player.is_player
								&& player.player_character.id == props.entity_id
							)
							|| (props.relationship && props.extensible)
							|| (props.location && props.extensible)
							|| adding_trait
						"
						:value="adding_trait ?
							player.small_buttons ? 'x' : 'stop adding trait x' :
							player.small_buttons ? '+' : 'add trait +'"
						@click="toggle_add_trait" />
				</div>

				<div class="add_trait" v-if="adding_trait">


					<div v-if="potential_traits.length == 0" class="no-results">no available traits to add</div>
					
					<div class="trait-list">
						<div class="trait-search" v-if="search_potential_traits_visible || potential_traits.length == 0">
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
						<div class="search-potential-trait-toggle" :class="search_potential_traits_visible ? 'active' : 'inactive'" v-if="potential_traits.length > 0">
							<div class="button" @click="search_potential_traits_visible = true" v-if="!search_potential_traits_visible">search for trait</div>
							<div class="button" @click="search_potential_traits_visible = false" v-else>x</div>
						</div>
						<template v-for="trait in potential_traits" :key="trait.id" v-if="potential_traits.length > 0">
							<div class="button potential-trait"
									:class="[trait.defaultTraitSetting?.rating && trait.defaultTraitSetting?.rating?.length > 0 ?
											trait.defaultTraitSetting?.rating.map((r) => r.rating)[0] : 'dn',
										trait.defaultTraitSetting?.rating && trait.defaultTraitSetting?.rating.map((r) => r.number_rating)[0] > 0 ?
											'positive' : 'negative']"
									@click="assign_trait_to_entity(trait)"
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
							<TraitEdit :trait_id="trait.id" :trait_name="trait.name" :expanded="true" v-if="player.is_gm && editing_potential_traits.includes(trait.id)" />
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
		<!-- </Transition> -->

	</div>
</template>

<style scoped>
	.traitset {
		&.active, &.next {
			width: 100%;
		}
		.set-title {
			text-align: center;
			font-size: large;
			cursor: pointer;
			/* padding: .4em 0; */
			justify-content: space-between;
			display: flex;
			z-index: 1;
			gap: 1em;
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
			.traitset-score {
				font-size: 1.2em;
				float: right;
				padding: .4em 1em;
				margin-left: .4em;
			}
			.traitset-explainer {
				display: inline;
			}
			.options {
				display: flex;
				justify-content: flex-end;
			}
		}
		.traitset-sfxs {
			position: relative;
			padding-left: 1.5em;
			border-bottom: 1px solid var(--color-border);
			display: flex;
			flex-wrap: wrap;
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
			display: block;
			overflow: hidden;
			.add-trait-button {
				max-height: 2em;
				background-color: var(--color-background-mute);
			}
		}
		.traits.hidden_title .explainer {
			padding: 0 2em 0 2em;
		}
		.add_trait {
			text-align: center;
			padding: 1em;
			.trait-search {
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
			.trait-search.creatable {
				.trait-search-query {
					border-radius: 10px 0 0 10px;
				}
			}
			.trait-list {
				display: flex;
				flex-wrap: wrap;
				justify-content: center;
				align-items: center;
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
					flex-grow: 1;
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
		&.editing-traits {
			.entity-traits {
				background-color: var(--color-editing-mute);
			}
		}
	}
	.traitset.active {
		.set-title {
			position: sticky;
			z-index: 2;
			top: -3px;
			padding: 0;
			justify-content: space-between;
			.title {
				font-weight: bold;
				align-content: end;
				flex-direction: column;
				.traitset-name {
					vertical-align: text-bottom;
				}
				.big-limiter {
					line-height: 1em;
					font-size: 2em;
					text-align: center;
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
	/* .traitset.gm .set-title {
		background-color: var(--color-highlight-mute) !important;
	}
	.traitset.ts-complications .set-title {
		background-color: var(--color-hitch-mute) !important;
		color: var(--color-hitch-text);
	} */
</style>

<style>
	.dark {
		.traitset {
			flex-grow: 1;
			border: 1px solid var(--color-border);
			border-radius: 10px;
			overflow: hidden;
			backdrop-filter: blur(5px);
			box-shadow: inset 0 0 10px var(--color-background-mute);
			.set-title {
				letter-spacing: .1em;
			}
			.traitset-info {
				.traitset-score {
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
				flex-wrap: wrap;
				flex-direction: column;
				padding: .4em;
			}
			.trait-divider {
				display: none;
			}
		}
		.traitset.active {
			.set-title {
				background-color: var(--color-highlight-mute);
				color: var(--color-highlight-text);
				text-shadow: none;
			}
		}
		.traitset.inactive {
			.set-title {
				/* color: var(--color-text); */
				background-color: var(--color-background-mute);
				justify-content: space-between;
				.title {
					gap: 1em;
				}
			}
		}
		.traitset.inactive.full {
			box-shadow: 0 0 10px var(--color-highlight);
			.trait-count,
			.title .traitset-name {
				color: var(--color-disabled);
				text-shadow: 0 0 4px var(--color-highlight);
			}
		}
		.traitset.inactive.next {
			border-top: 1px solid var(--color-border);
		}
		.entity-traits {
			display: flex;
			flex-wrap: wrap;
			padding: .2em;
			gap: .4em;
		}
	}
	.dark.has-image {
		.traitset.active .set-title {
			background-color: var(--color-background-mute);
			color: var(--color-text);
		}
		.traitset.active .traits {
			/* box-shadow: inset 0 0 20px var(--color-background-mute); */
		}
	}
	.dark.editing {
		.traitset.active .set-title {
			background-color: var(--color-editing-mute);
			color: var(--color-editing-text);
		}
		.traitset.active .traits {
			box-shadow: inset 0 0 10px var(--color-editing-mute);
			border: 1px solid var(--color-editing-mute);
		}
	}
	.light {
		.traitset.active {
			border-top: 1px solid var(--color-border);
			border-bottom: 1px solid var(--color-border);
			.set-title {
				background-color: var(--color-background);
				border-bottom: 3px double var(--color-text);
			}
		}
		.traitset.active.minimal {
			border: none;
		}
		.traitset.inactive.next {
			background-color: var(--color-background);
			border-top: 1px solid var(--color-border);
		}
		.traitset.gm .set-title {
			background-color: var(--color-highlight-mute);
		}
		.traitset.ts-complications .set-title {
			background-color: var(--color-hitch-mute);
		}
	}
	.triptych {
		.traitset.inactive.next {
			position: sticky;
			bottom: 47px;
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
