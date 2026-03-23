<script setup lang="ts">
	/*
		a location item
		as displayed in a character's location/locale list
		or in location overview
		displays collapsible hierarchy
	*/
	import { marked } from 'marked'

	import {
		ref,
		type Ref,
		computed,
		watch,
		onMounted,
		onUnmounted,
		nextTick
	} from 'vue'
	import { useRoute } from 'vue-router'
	import { useElementBounding, useWindowSize } from '@vueuse/core'

	import { usePlayerStore } from '@/stores/PlayerStore'
	import { useDicepoolStore } from '@/stores/DicepoolStore'

	import Traitset from '@/components/Traitset.vue'
	import EntityButton from './EntityButton.vue'
	import EntityNewButton from './EntityNewButton.vue'
	import Location from '@/components/Location.vue'
	import Presence from '@/components/Presence.vue'
	import EntityCard from '@/components/EntityCard.vue'
	// const LocationItem = defineAsyncComponent(() => import('@/components/Location.vue'))

	import { useLocation } from '@/composables/Location'
	import { useEntityList } from '@/composables/EntityList'

	import type { Entity, Location as LocationType } from '@/interfaces/Types'

	const route = useRoute()
	const player = usePlayerStore()
	const { resolutions } = useDicepoolStore()
	
	const props = defineProps<{
		loc: string,
		level: number,
		show_levels?: number,
		zone?: boolean,
		transversable?: boolean,
		scroll_y?: number,
		active_entity_id?: string,
		parent_left?: number,
		parent_width?: number
	}>()

	const emit = defineEmits([
		'transverse',
		'show_entity',
		'scroll_to_top'
	])

	const {
		location,
		retrieve_location,
		retrieve_small_location,
		retrieve_presence,
		retrieve_neighboring_presence,
		add_location_relationship,
		create_zone,
		update_location,
		make_transversable,
		set_location_visibility,
		import_entity,
		imagen
	} = useLocation(undefined, props.loc)

	retrieve_small_location()

	const is_current_location = computed(() => {
		if(!player.is_gm && player.player_character?.location) {
			return props.loc == player.player_character.location.key
		}
		else if(player.is_gm && player.perspective?.location) {
			return props.loc == player.perspective.location.key
		}
		else { return false }
	})

	const title_pulsate = ref(false)
	const held = ref(false)

	const editing_location = ref(false)
	const editing_description = ref(false)
	function toggle_editing_description() {
		new_flavortext.value = location.value.flavortext
		editing_description.value = !editing_description.value
	}
	const editing_presence = ref(false)
	const editing_traits = ref(false)
	function toggle_editing_traits() {
		editing_traits.value = !editing_traits.value
	}
	const editing_zones = ref(false)
	function toggle_editing_zones() {
		editing_zones.value = !editing_zones.value
	}

	const new_location_name = ref(location.value.name)
	const location_name_edit_ref = ref<HTMLInputElement>()

	function longpress_location_header() {
		held.value = true
		new_location_name.value = location.value.name
		new_flavortext.value = location.value.flavortext
		editing_location.value = !editing_location.value
		title_pulsate.value = true
		nextTick(() => {
			if(location_name_edit_ref.value) {
				location_name_edit_ref.value.focus()
			}
		})
		setTimeout(() => {
			held.value = false
		}, 500)
	}

	function update_name() {
		update_location({ name: new_location_name.value })
		editing_location.value = false
	}

	const show_location_image = ref(false)

	function click_title() {
		if(props.transversable) {
			transverse(location.value)
		}
		else {
			if(!show_location_image.value && overwrite_active.value != location.value.id) {
				show_location_image.value = true
				show_active.value = player.is_gm
				overwrite_active.value = location.value.id
			}
			else {
				show_active.value = false
				overwrite_active.value = undefined
				show_location_image.value = false
			}
		}
	}

	function click_zone(zone: LocationType) {
		transverse(zone)
	}

	function transverse(loc: LocationType) {
		if(player.the_entity?.id != loc.id) {
			console.log("transversing to " + loc.name)
			emit('transverse', loc)
		}
	}

	const expanded = ref(props.level < (props.show_levels ?? 2))

	function polling() {
		if(
			polling_active.value
			&& expanded.value
			&& location.value.key != 'placeholder'
			&& player.the_entity?.location?.key == props.loc
			&& player.playing
		) {
			console.log(new Date().toTimeString() + " polling location " + location.value.name)
			entity_button_refs_left.value = []
			entity_button_refs_right.value = []
			retrieve_presence()

			if(
				player.the_entity?.following &&
				!location.value.entities?.map(e => e.id).includes(player.the_entity?.following.id ?? '')
			) {
				// changed player location
				player.is_player ? player.retrieve_character() : player.retrieve_perspective()
				console.log("changed player location during polling to " + player.the_entity?.location?.key)
				router.push({ path: '/location/' + player.the_entity?.location?.key })
			}

		}
		if(polling_active.value) setTimeout(polling, 10000)
	}

	const polling_active = ref(expanded.value)

	polling()

	// watch(() => player.playing, (newVal, oldVal) => {
	// 	if(newVal == true) {
	// 		polling()
	// 	}
	// })

	// this is to push entity button update after presence change
	const entity_button_refs_left = ref([] as any)
	const entity_button_refs_right = ref([] as any)

	watch(() => location.value.entities, (newVal, oldVal) => {
		if(
			newVal != oldVal
			&& player.the_entity?.location?.key == props.loc
			&& (
				!newVal?.map(e => e.id).includes(player.the_entity?.id ?? '')
				|| (player.the_entity?.following && !newVal?.map(e => e.id).includes(player.the_entity?.following.id ?? ''))
			)
			&& !(
				// compare the newVal and the oldVal arrays, only check id's
				newVal?.map(e => e.id).join(',') == oldVal?.map(e => e.id).join(',')
			)
		) {
			console.log("changing player location")
			player.is_player ? player.retrieve_character() : player.retrieve_perspective()
			console.log("presence changed from " + oldVal?.map(e => e.name) + " to " + newVal?.map(e => e.name) + ", changed player location to " + player.the_entity?.location?.key)
		}

		if(newVal) {
			// update entity buttons (entity.active)
			for(let i = 0; i < newVal.length; i++) {
				const left_entity = entity_button_refs_left.value.filter(eb => eb.entity.id == newVal[i].id)
				const right_entity = entity_button_refs_right.value.filter(eb => eb.entity.id == newVal[i].id)
				if(left_entity.length > 0 && newVal[i].active != left_entity[0].entity.active) {
					console.log("updating entity " + newVal[i].name + " active from " + left_entity[0].entity.active + " to " + newVal[i].active)
					entity_button_refs_left.value.filter(eb => eb.entity.id == newVal[i].id)[0].entity = {
						...entity_button_refs_left.value.filter(eb => eb.entity.id == newVal[i].id)[0].entity,
						active: newVal[i].active
					}
				}
				if(right_entity.length > 0 && newVal[i].active != right_entity[0].entity.active) {
					console.log("updating entity " + newVal[i].name + " active from " + right_entity[0].entity.active + " to " + newVal[i].active)
					entity_button_refs_right.value.filter(eb => eb.entity.id == newVal[i].id)[0].entity = {
						...entity_button_refs_right.value.filter(eb => eb.entity.id == newVal[i].id)[0].entity,
						active: newVal[i].active
					}
				}
			}
			entity_button_refs_left.value = []
			entity_button_refs_right.value = []
		}
	})

	const presence = computed(() => {
		return location.value.entities?.filter(e =>
			e.entityType != 'location'
			&& (
				player.is_gm
				|| (e.entityType == 'character' && e.active)
				|| (
					e.entityType == 'npc' && (
						e.hidden === false
						|| e.knownTo?.map(kt => kt.id).includes(player.player_character?.id ?? '')
						|| e.active
					)
				)
				|| e.entityType == 'asset'
				|| e.entityType == 'faction'
			) && !e.isArchetype
			// ) && !(
			// 	e.isArchetype && player.is_player
			// )
		)
	})

	// show_active true shows the active NPC prominently
	const show_active = ref(true)
	const overwrite_active = ref<string>()
	const active_npc = computed(() => {
		if(player.is_gm) {
			if(resolutions.filter(r => !r.player.is_gm).length > 0) {
				const entityIds = resolutions.filter(r => !r.player.is_gm)[0].dice.map(d => d.entityId);
				const entityIdCounts = {} as any;
				entityIds.forEach(id => entityIdCounts[id] = (entityIdCounts[id] || 0) + 1);
				const entityId = Object.keys(entityIdCounts).reduce((a, b) => entityIdCounts[a] > entityIdCounts[b] ? a : b);
				return entityId
			}
		}
		if(presence.value && presence.value.filter(e => e.active && ['npc', 'asset', 'faction'].includes(e.entityType)).length > 0) {
			return presence.value?.filter(e => e.active && ['npc', 'asset', 'faction'].includes(e.entityType))[0].id
		}
	})
	watch(active_npc, (newNPC, oldNPC) => {
		if(newNPC != oldNPC) {
			overwrite_active.value = undefined
		}
	})
	watch(() => props.active_entity_id, (newId) => {
		overwrite_active.value = newId ?? ""
	})
	watch(overwrite_active, (newId, oldId) => {
		if(newId && newId != oldId) {
			show_location_image.value = false
			show_active.value = true
		}
	})

	const filtered_zones = computed(() => {
		return location.value.zones?.filter(z =>
			!z.hidden
			|| z.knownTo?.map(kt => kt.id).includes(player.player_character?.id ?? '')
			|| player.is_gm
		)
	})

	async function add_to_codex() {
		if(player.the_entity) {
			await add_location_relationship(player.the_entity.id)
			player.is_gm ? player.retrieve_perspective_relations('network-only') : player.retrieve_character_relations('network-only')
		}
	}



	// flavortext
	const clipped_flavortext = ref(false)

	const rendered_flavortext = computed(() => {
		if(location.value.flavortext) {
			let text = location.value.flavortext
			if(clipped_flavortext.value) {
				text = location.value.flavortext.slice(0, 200) +
						(location.value.flavortext.length > 200 ? '...' : '')
			}
			return marked.parse(text)
		}
	})

	const new_flavortext = ref(location.value.flavortext)
	watch(player, () => {
		if(player.editing) {
			new_flavortext.value = location.value.flavortext
		}
	})

	function update_flavortext() {
		update_location({ description: new_flavortext.value })
	}




	const newZone: Ref<string> = ref("")
	
	import { useRouter } from 'vue-router'
    const router = useRouter()

	import useClipboard from 'vue-clipboard3'
	const { toClipboard } = useClipboard()
	const copy = async () => {
		try {
			await toClipboard(location.value.id)
			console.log('Copied to clipboard')
		} catch (e) {
			console.error(e)
		}
	}

	const image_link = ref(
		'/assets/uploads/' + location.value.image?.path + '/' +
		(player.data_saving ? 'small' : 'large') +
		location.value.image?.ext)
	const image_link_small = ref(
		'/assets/uploads/' + location.value.image?.path +
		'/small' + location.value.image?.ext)
	const gradient = ref('100%')
	const show_small_image = ref(player.data_saving)
	watch(expanded, (newExpanded) => {
		if(newExpanded) {
			gradient.value = '200%'
		}
		else {
			gradient.value = '100%'
		}
	})
	watch(() => location.value.image, (newImage) => {
		if(newImage) {
			image_link.value = '/assets/uploads/' + newImage.path +
				'/' + (player.data_saving ? 'small' : 'large') +
				newImage.ext
			image_link_small.value = '/assets/uploads/' + newImage.path +
				'/small' + newImage.ext
		}
	})

	function establish_route() {
		if(player.the_entity) {
			make_transversable(player.the_entity.id)
			setTimeout(() => player.retrieve_perspective_relations(), 200)
		}
	}

	const show_flavortext = ref(true)
	function click_description_header() {
		show_flavortext.value = !show_flavortext.value
	}
	function rightclick_description_header() {
		if(player.is_gm) {
			toggle_editing_description()
		}
	}

	const { entities, search_entities } = useEntityList(undefined, undefined)
	const show_import = ref(false)
	const import_search = ref<string>('')
	function toggle_import() {
		if(!show_import.value) {
			retrieve_neighboring_presence()
		}
		else {
			import_search.value = ''
		}
		show_import.value = !show_import.value
	}
	function search_import() {
		search_entities(import_search.value)
	}
	function import_ett(entity_id: string) {
		import_entity(entity_id)
		toggle_import()
		overwrite_active.value = entity_id
	}

	function hide_location() {
		set_location_visibility()
		editing_location.value = false
	}

	function switch_perspective(entity_id: string) {
		player.set_perspective(entity_id)
	}

	onUnmounted(() => {
		console.log("unmounting location " + location.value.name + ", disabling polling")
		polling_active.value = false
	})

	if(expanded.value) {
		retrieve_location()
		console.log("mounted location " + location.value.name + "")
	}

	const zones = ref()
	const { top } = useElementBounding(zones)
	const { height: window_height } = useWindowSize()

	const background_image_width = computed(() => {
		return Math.max(
			location.value.image?.width ?? 0,
			props.parent_width ?? 0,
			window_height.value * (location.value.image?.width ?? 0) / (location.value.image?.height ?? 1)
		)
	})
	const background_image_height = computed(() => {
		return Math.max(
			location.value.image?.height ?? 0,
			window_height.value,
			(props.parent_width ?? 0) * (location.value.image?.height ?? 0) / (location.value.image?.width ?? 1)
		)
	})

	const filter_degree = computed(() => {
		// Calculate the degree of filter effect applied based on the position of the zones element
		// If the top of the zones element is below the middle of the window height or there are no zones, no filter is applied
		if((top.value > window_height.value / 2) || (location.value.zones && location.value.zones.length == 0)) {
			return 0
		}
		// If the top of the zones element is above the viewport, apply maximum filter effect
		if(top.value < 0) {
			return 1
		}
		// Otherwise, calculate a proportional filter effect based on the vertical position
		return 1 - (top.value / (window_height.value / 2))
	})
	const filter = computed(() => 'contrast(' + (1 - filter_degree.value * 0.2) + ')'
		+ ' grayscale(' + (filter_degree.value * 0.6) + ')'
		+ ' blur(' + (filter_degree.value * 2) + 'px)')
	
	const location_element = ref()
	function change_active(entity_id: string) {
		overwrite_active.value = entity_id
		emit('scroll_to_top')
	}

	function set_presence_watcher(new_clone: Entity) {
		console.log("created clone " + JSON.stringify(new_clone))
		console.log("changed player perspective to " + new_clone.name)
		retrieve_presence()
		player.set_perspective(new_clone.id)
	}

	const show_parents = ref(false)
	const show_transversables = ref(false)
	const show_zones = ref(false)
</script>

<template>
	<div class="location-component"
			:class="[
				expanded ? 'is-expanded' : 'is-not-expanded',
				location.image ? 'has-image' : 'no-image',
				{ 'hidden': location.hidden && player.is_gm },
				{ 'zone': props.zone },
				player.is_gm ? 'gm' : 'player',
			]"
			:style="{ backgroundImage: `url('${show_small_image ? image_link_small : image_link}')`}"
			ref="location_element">
		<div class="location-component-wrapper">
			<div class="title expand-zones"
					:class="[
						{ 'header': is_current_location },
					]"
					v-if="location"
					@click="click_title"
					@click.right="longpress_location_header"
					@contextmenu="(e: MouseEvent) => e.preventDefault()">
				
				<component :is="'h' + (props.level + 2)" class="location-name"
						:class="{ 'text-pulsate': title_pulsate }"
						@animationend="title_pulsate = false"
						v-touch:hold="longpress_location_header"
						v-if="!editing_location">
					{{ location.name != 'placeholder' ? location.name : 'transversal' }}
				</component>

				<input type="text" class="header location-name"
					ref="location_name_edit_ref"
					v-model="new_location_name"
					v-show="editing_location && player.is_gm"
					@click.stop />
				<input type="button" class="button" value="save"
					v-if="location.name != new_location_name && editing_location"
					@click.stop="update_name" />

				<input type="button" class="button transverse-button corner-button"
					:value="player.small_buttons ? '⬇' : '⬇\ntransverse'"
					v-if="!is_current_location
						&& player.is_gm
						&& player.perspective
						&& player.the_entity?.id != location.id
						&& editing_location"
					@click.stop="transverse(location)" />

				<input type="button" class="button link-button corner-button"
					:value="player.small_buttons ? '🗺' : '🗺\ntake perspective'"
					@click.stop="switch_perspective(location.id)"
					v-if="player.is_gm && route.params.id != location.key && editing_location" />
				
				<input type="button" class="button codex-button corner-button"
					:value="player.small_buttons ? '🏷' : '🏷\nadd to contacts'"
					@click.stop="add_to_codex"
					v-if="player.the_entity
						&& player.the_entity.id != location.id
						&& !player.the_entity.relations?.map(e => e.toEntity.id).some(id => id == location.id)
						&& editing_location
					" />

				<input type="button" class="button transversable-button corner-button"
					:value="player.small_buttons ? '⤠' : '⤠\nmake transversable'"
					@click.stop="establish_route"
					v-if="player.the_entity
						&& player.the_entity.entityType == 'location'
						&& player.the_entity?.entityType == 'location'
						&& player.the_entity.id != location.id
						&& editing_location
					" />

				<input type="button" class="button hide-button corner-button" :class="location.hidden ? 'visible' : 'hidden'"
					:value="location.hidden ? (player.small_buttons ? '🌑' : '🌑\nhiding location') : player.small_buttons ? '🌕' : '🌕\nshowing location'"
					@click.stop="hide_location"
					v-if="player.is_gm && editing_location" />
				
				<input type="button" class="copy-id button corner-button" title="copy location id"
					@click.stop="copy"
					:value="player.small_buttons ? '#' : '#\ncopy id'"
					v-if="player.is_gm && editing_location" />
				
				<input type="button" class="imagen-button button corner-button" @click.stop="imagen(true)"
					:value="player.small_buttons ? '📷' : '📷\nimage'"
					v-if="player.is_gm && editing_location" />

			</div>

			<div class="content" v-if="expanded">
				<div class="left">
					<div class="presence attribute" v-if="presence && presence.length > 0">
						<EntityButton
							class="entity-card"
							v-if="presence && presence.length > 1"
							v-for="entity in presence.slice(Math.ceil(presence.length / 2))"
							:key="entity.key"
							:ref="el => entity_button_refs_left.push(el)"
							:entity_id="entity.id"
							options_direction="right"
							:show_name="false"
							override_click
							@click_entity="(active_npc == entity.id && overwrite_active == 'empty') || overwrite_active != entity.id ?
								overwrite_active = entity.id : overwrite_active = 'empty'" />
						<EntityNewButton
							:location_id="location.id"
							options_direction="right"
							@created_entity="retrieve_presence"
							v-if="player.is_gm" />
					</div>
				</div>
				<div class="center">
					<div class="archetypes">
						<EntityButton
							class="entity-card"
							v-for="archetype in location.entities?.filter(e => e.isArchetype)"
							:key="archetype.key"
							:entity_id="archetype.id"
							:show_name="false"
							show_archetypes
							@show_entity="(entity_key: string) => emit('show_entity', entity_key)"
							override_click @click_entity="(active_npc == archetype.id && overwrite_active == 'empty') || overwrite_active != archetype.id ?
								overwrite_active = archetype.id : overwrite_active = 'empty'" />
					</div>
					<div class="active-npc-wrapper" v-if="show_active && (active_npc || overwrite_active) && overwrite_active != 'empty' && !show_location_image">
						<EntityCard
							class="active-npc"
							:entity_id="overwrite_active ?? active_npc"
							@hide_entity="overwrite_active = 'empty'"
							@show_entity="(entity_key) => emit('show_entity', entity_key)"
							@instantiated_entity="set_presence_watcher" />
					</div>
					<div class="location-image-wrapper" v-if="show_location_image">
						<img class="location-image" :src="image_link" @click="show_location_image = false" />
					</div>
				</div>
				<div class="right">
					<div class="presence attribute" v-if="presence && presence.length > 0">
						<EntityButton
							class="entity-card"
							v-if="presence && presence.length > 0"
							v-for="entity in presence.slice(0, Math.ceil(presence.length / 2))"
							:key="entity.key"
							:ref="el => entity_button_refs_right.push(el)"
							:entity_id="entity.id"
							options_direction="left"
							:show_name="false"
							override_click
							@click_entity="(active_npc == entity.id && overwrite_active == 'empty') || overwrite_active != entity.id ?
								overwrite_active = entity.id : overwrite_active = 'empty'" />
					</div>
				</div>
			</div>
			<div class="entities attribute" v-if="player.is_gm && expanded">
				<div class="attribute-header header" @click="editing_presence = !editing_presence">
					<span>presence</span>
					<div class="border-bottom"></div>
				</div>
				<div class="import-entities drawer" v-if="editing_presence">
					<div class="import">
						<div class="search" v-if="player.is_gm">
							<input type="text" class="import-search-text" placeholder="import entity" v-model="import_search" />
							<input type="button" class="button" value="search" v-if="import_search" @click="search_import" />
						</div>
						<div class="entity-cards" v-if="import_search">
							<EntityButton v-for="entity in entities"
								:key="entity.key"
								:entity_id="entity.id"
								override_click
								is_active
								@click_entity="change_active(entity.id)" />
						</div>
					</div>
					<div class="neighboring">
						<div class="show-parent-wrapper show-presence-button-wrapper">
							<input type="button" class="button-mnml show-presence-button header" value="toggle parents" @click="show_parents = !show_parents" />
						</div>
						<Presence class="parent-location" v-for="(neigbor_location, index) in location.parents?.slice(1, 4).reverse() ?? []"
								:key="neigbor_location.key"
								v-if="show_parents"
								:location_key="neigbor_location.key"
								:search="import_search"
								:level="3 - index"
								@click_entity="(ett_id) => change_active(ett_id)"
								@transverse="transverse" />
						<div class="show-transversable-wrapper show-presence-button-wrapper">
							<input type="button" class="button-mnml show-presence-button header" value="toggle transversables" @click="show_transversables = !show_transversables" />
						</div>
						<Presence class="transversable-location" v-for="neigbor_location in location.transversables ?? []"
								:key="neigbor_location.key"
								v-if="show_transversables"
								:location_key="neigbor_location.key"
								:search="import_search"
								:level="0"
								@click_entity="(ett_id) => change_active(ett_id)"
								@transverse="transverse" />
						<div class="show-current-wrapper show-presence-button-wrapper">
							<input type="button" class="button-mnml show-presence-button header" value="current location" />
						</div>
						<Presence
								:key="location.key"
								:location_key="location.key"
								:search="import_search"
								:level="0"
								@click_entity="(ett_id) => change_active(ett_id)" />
						<div class="below-line show-presence-button-wrapper">
							<input type="button" class="button-mnml show-presence-button header" value="toggle zones" @click="show_zones = !show_zones" />
						</div>
						<Presence class="zone-location" v-if="show_zones" v-for="neigbor_location in location.zones ?? []"
								:key="neigbor_location.key"
								:location_key="neigbor_location.key"
								:search="import_search"
								:level="-1"
								@click_entity="(ett_id) => change_active(ett_id)"
								@transverse="transverse" />
					</div>
				</div>
			</div>
			<div class="description attribute" v-if="player.is_gm && expanded">
				<div class="attribute-header header" @click="click_description_header" @click.right.prevent="rightclick_description_header">
					<span>description</span>
					<div class="border-bottom"></div>
				</div>
				<div class="attribute-body"
						v-if="show_flavortext && (rendered_flavortext || new_flavortext || editing_description)">
					<span class="flavortext" v-html="rendered_flavortext"
						v-if="!editing_description && player.is_gm"
						@click.right="toggle_editing_description"
						v-touch:longtap="toggle_editing_description"
						@contextmenu="(e) => e.preventDefault()" />
					<textarea class="flavortext" v-model="new_flavortext"
						v-if="(player.editing || editing_description) && player.is_gm" />
					<img class="location-portrait" v-if="location.image && clipped_flavortext"
						:src="image_link_small" @click="clipped_flavortext = !clipped_flavortext" />
					<input type="button" class="button save" value="save"
						@click="update_flavortext"
						v-if="(player.editing || editing_description) && location.flavortext != new_flavortext" />
					<div class="border-bottom"></div>
				</div>
			</div>
			<div class="traits attribute" v-if="expanded">
				<div class="attribute-header header"
						@click="toggle_editing_traits"
						@click.right="toggle_editing_traits"
						v-touch:longtap="toggle_editing_traits"
						@contextmenu="(e) => e.preventDefault()">
					<span>location traits</span>
					<div class="border-bottom"></div>
				</div>
				<div class="attribute-body">
					<Suspense>
						<Traitset
							v-for="traitset in location.traitsets?.filter(ts => player.is_gm ? true : !ts.entityTypes?.includes('gm'))"
							:key="traitset.id"
							:traitset_id="traitset.id"
							:entity_id="location.id"
							:location_key="props.loc"
							:limit="traitset.limit"
							:expanded="!editing_traits"
							:visible="editing_traits"
							:hide_title="!editing_traits"
							:extensible="editing_traits"
							:location="true"
							:polling="player.the_entity?.location?.key == props.loc
								&& (
									traitset.id == 'Traitsets/3' // assets
									|| traitset.id == 'Traitsets/906502' // resources
								)"
							@refetch="retrieve_location"
						/>
					</Suspense>
				</div>
			</div>
			<div class="zones attribute" v-if="expanded && (player.is_gm || (location.zones && location.zones.length > 0))" ref="zones">
				<div class="attribute-header header"
						@click="toggle_editing_zones"
						@click.right="toggle_editing_zones"
						v-touch:longtap="toggle_editing_zones"
						@contextmenu="(e) => e.preventDefault()">
					<span>zones</span>
					<div class="border-bottom"></div>
				</div>
				<div class="attribute-body" v-if="(location.zones && location.zones.length > 0) || (player.is_gm && (player.editing || editing_zones))">
					<div class="location-component new-location" v-if="player.is_gm && (player.editing || editing_zones)">
						<input class="new-zone" type="text" placeholder="create zone" v-model="newZone" />
						<input type="button" class="button" v-if="newZone" value="create zone"
							@click="create_zone(newZone); newZone = ''" />
					</div>
					<Location v-for="zone in filtered_zones" :key="zone.key"
						:loc="zone.key"
						:level="props.level + 1"
						:show_levels="props.show_levels"
						:parent_left="props.parent_left"
						:parent_width="props.parent_width"
						zone
						transversable
						@transverse="(loc) => transverse(loc)" />
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
	.location-component {
		background-size: auto;
		flex-grow: 1;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		position: relative;
		overflow: hidden;
		min-height: 300px;
		.location-component-wrapper {
			width: 100%;
			.title {
				cursor: pointer;
				display: flex;
				flex-direction: column;
				.location-name {
					font-size: 2em;
					background-color: transparent;
				}
				.location-name-edit {
					text-align: center;
				}
				.corner-button {
					z-index: 2;
					position: absolute;
					margin: 0;
					font-size: 1.2em;
				}
				.imagen-button {
				}
				.link-button {
					top: 0;
					left: 0;
					border-top: none;
					border-left: none;
					border-radius: 0 0 10px 0;
				}
				.codex-button {
					top: 0;
					right: 0;
					border-top: none;
					border-right: none;
					border-radius: 0 0 0 10px;
				}
				.transversable-button {
					top: 50%;
					right: 0;
					transform: translateY(-50%);
					border-top: none;
					border-right: none;
					border-radius: 10px 0 0 10px;
				}
				.transverse-button {
					bottom: 0;
					left: 0;
					border-bottom: none;
					border-left: none;
					border-radius: 0 10px 0 0;
				}
				.copy-id {
					bottom: 0;
					right: 0;
					border-bottom: none;
					border-right: none;
					border-radius: 10px 0 0 0;
				}
				.hide-button {
					left: 0;
					top: 50%;
					transform: translateY(-50%);
					border-left: none;
					border-radius: 0 10px 10px 0;
					&.visible {
						color: transparent;
						text-shadow: 0 0 1px var(--color-text);
					}
				}
			}
		}
		.content {
			padding: 0 1em 3em;
			display: grid;
			grid-template-columns: 60px auto 60px;
			width: 100%;
			.left, .right {
				width: 60px;
				z-index: 1;
				display: flex;
				flex-direction: column;
				/* justify-content: space-around; */
				gap: 1em;
				.presence {
					padding-top: 10%;
					max-height: 90%;
					width: 60px;
					display: flex;
					flex-direction: column;
					align-items: center;
					justify-content: space-between;
					gap: 1em;
					.entity-card {
						width: 50px;
						/* height: 70px; */
					}
				}
			}
			.center {
				flex-grow: 1;
				display: flex;
				flex-direction: column;
				overflow-x: hidden;
				.archetypes {
					display: flex;
					flex-wrap: wrap;
					justify-content: center;
					gap: 1em;
					/* overflow-x: auto; */
					padding: 1em;
					.entity-card {
						width: 50px;
						min-width: 50px;
						/* height: 70px; */
						/* overflow: hidden; */
					}
				}
				.active-npc-wrapper {
					display: flex;
					flex-direction: column;
					/* justify-content: center; */
					align-items: center;
					.active-npc {
						max-width: 90%;
						max-height: 100%;
						margin: 20px 0;
					}
				}
			}
		}
		.neighboring {
			.show-presence-button-wrapper {
				width: 100%;
				display: flex;
				justify-content: center;
				/* background-color: var(--color-background-mute); */
				background-image: linear-gradient(to bottom, var(--color-background-soft) 45%, white 50%, var(--color-background-soft) 55%);
				.show-presence-button {
					background-color: var(--color-background-soft);
				}
			}
		}
		.attribute {
			.attribute-header {
				text-align: center;
				position: relative;
				font-size: 1.2em;
				padding-top: .4em;
				.edit-button {
					position: absolute;
					top: 0;
					right: 0;
				}
			}
			&.entities {
				.drawer {
					border: 1px solid var(--color-border);
					position: relative;
					.expand-title {
						cursor: pointer;
					}
					.neighboring {
						display: flex;
						flex-wrap: wrap;
						/* gap: .4em; */
						.below-line {
							width: 100%;
						}
					}
					.search {
						display: flex;
						justify-content: center;
						flex-wrap: nowrap;
						.import-search-text {
							flex-grow: 2;
							font-size: 1.2em;
							margin: .4em 0;
						}
						.button {
							flex-grow: 1;
						}
					}
				}
				.drawer.expanded {
					padding: 1em;
				}
				.import-entities {
					.entity-cards {
						display: flex;
						flex-wrap: wrap;
						justify-content: center;
						gap: 1em;
					}
				}
			}
			&.description {
				position: relative;
				.flavortext {
					display: block;
					padding: 1em;
					min-width: 100%;
				}
				textarea.flavortext {
					min-height: 100px;
				}
				.location-portrait {
					max-height: 240px;
					border: 5px solid var(--color-background);
				}
			}
		}
		&.hidden {
			&.is-not-expanded {
				box-shadow: inset 0 0 30px var(--color-text);
				/* border: 2px solid var(--color-text); */
				opacity: 0.5;
				>.location-component-wrapper >.title .location-name {
					/* text-shadow: 0 0 3px var(--color-text);
					color: transparent; */
					/* text-shadow: 0 0 50px var(--color-background), 0 0 50px var(--color-background), 0 0 100px var(--color-background); */
				}
			}
			&.is-expanded {
				>.title .location-name {
					color: var(--color-disabled);
				}
			}
		}
		&.player {
			.content {
				min-height: 80vh;
			}
			.zones {
				padding: 1em;
				&>.attribute-body {
					display: flex;
					flex-direction: column;
					gap: 1em;
					.zone {
						/* background-position: center; */
						display: flex;
						justify-content: center;
						align-items: center;
						/* box-shadow: inset 0 0 20px var(--color-background-mute); */
					}
				}
			}
		}
		&.gm {
			.zones {
				/* padding: 3%; */
				&>.attribute-body {
					display: flex;
					flex-wrap: wrap;
					gap: 1em;
					padding: 1em;
					.zone {
						min-height: 300px;
						min-width: 300px;
						/* background-position: center; */
						display: flex;
						justify-content: center;
						align-items: center;
						/* background-size: 33vw; */
						/* box-shadow: inset 0 0 20px var(--color-background-mute); */
					}
				}
			}
		}
		&.no-image {
			background-color: var(--color-background-mute);
		}
		&.is-not-expanded {
			margin: .2em;
			.location-component-wrapper {
				height: 100%;
				.title {
					position: relative;
					width: 100%;
					height: 100%;
					white-space: preline;
					/* line-height: 4em; */
					/* padding: 4em 3em; */
					display: flex;
					flex-direction: column;
					justify-content: center;
					.corner-button {
						display: flex;
						position: absolute;
						margin: 0;
						font-size: 1.2em;
						&.imagen-button {
							bottom: 0;
							left: 50%;
							transform: translateX(-50%);
							border-radius: 10px 10px 0 0;
						}
					}
				}
			}
		}
		&.is-expanded {
			position: relative;
			&.player {
				min-height: 75vh;
			}
			/* border: 1px solid var(--color-background); */
			width: 100%;
			>.location-component-wrapper {
				>.title {
					padding: 1em 3em 0 3em;
					.location-name {
						flex-grow: 2;
					}
					.button.save {
						position: initial;
					}
					.transverse-button {
						top: 10em;
						left: 0;
						bottom: unset;
						border-bottom: none;
						border-left: none;
						border-radius: 0 10px 10px 0;
					}
					.hide-button, .imagen-button {
						top: 5.5em;
					}
					/* .hide-button {
						border-bottom: none;
						border-right: none;
					} */
					.imagen-button {
						right: 0;
						border-top: none;
						border-left: none;
						border-radius: 10px 0 0 10px;
					}
					.copy-id {
						top: 10em;
						right: 0;
						bottom: unset;
						border-bottom: none;
						border-right: none;
						border-radius: 10px 0 0 10px;
					}
				}
			}
		}
		&.new-location {
			justify-content: center;
			.new-zone {
				text-align: center;
				font-size: 1.2em;
				padding: 1em;
			}
		}
	}
</style>

<style>
	.dark {
		.location-component {
			border-radius: 60px;
			background-attachment: fixed;
			background-position-x: v-bind(parent_left + 'px');
			background-position-y: top;
			/* background-size: v-bind(parent_width + 'px') auto; */
			background-size: v-bind(background_image_width + 'px') v-bind(background_image_height + 'px');
			box-shadow: 0 0 10px var(--color-background);
			&.is-expanded {
				background-color: transparent;
				.entities {
					.drawer {
						box-shadow: inset 0 0 100px var(--color-background);
					}
				}
				>.location-component-wrapper {
					backdrop-filter: v-bind('filter');
				}
				.zones .location-component {
					border-radius: calc(60px - 1em);
				}
			}
			div.content div.center {
				div.location-image-wrapper img {
					max-width: 100%;
					box-shadow: 0 0 10px var(--color-background);
				}
				.archetypes .entity-card {
					height: 70px;
				}
			}
			.entities {
				padding: 0 0 1em 0;
			}
			.border-bottom {
				height: 1px;
				background-image: linear-gradient(to right, var(--color-border), var(--color-text) 50%, var(--color-border) 90%);
				box-shadow: 0 0 10px var(--color-background);
			}
			&.zone {
				box-shadow: inset 0 0 10px -5px var(--color-background-mute),
					inset 0 0 20px var(--color-background-mute),
					inset 0 0 30px var(--color-background-mute);
			}
			&.has-image {
				/* text-shadow: var(--text-shadow); */
				.flavortext, .corner-button {
					color: var(--color-text);
				}
				.title .location-name, .header, .corner-button {
					text-shadow: var(--color-background) 0px 0px 2px,
						var(--color-background) 0px 0px 4px,
						var(--color-background) 0px 0px 8px,
						var(--color-background) 0px 0px 2px;
				}
				.flavortext {
					text-shadow: var(--text-shadow), var(--text-shadow);
					box-shadow: inset 0 0 200px var(--color-background);
					backdrop-filter: blur(20px);
				}
			}
			&.new-location {
				background-color: var(--color-background-mute);
			}
		}
		.location-component.has-image.is-not-expanded .title .button {
			background-color: var(--color-background-mute);
		}
	}
	.dark.triptych {
		#current-location .location-component, .zone {
			background-size: cover;
		}
	}
	.light {
		.location-component {
			border: 1px solid var(--color-border);
			div.content div.center div.location-image-wrapper img {
				border: 3px double var(--color-border);
				max-width: calc(100% - 2em);
				margin: 1em;
				background-color: var(--color-background);
			}
			.location-attribute {
				border-top: 3px double var(--color-border);
				border-bottom: 3px double var(--color-border);
			}
			.description {
				background-color: var(--color-background);
				margin-top: .4em;
			}
			.entities {
				padding: 1em .4em;
				background-color: var(--color-background);
			}
			.zones {
				background-color: var(--color-background);
			}
			&.has-image {
				background-position: top center;
				background-size: 100vw auto;
				.title .location-name {
					background-color: var(--color-background);
					border: 3px double var(--color-border);
				}
				.traits {
					background-color: var(--color-background-mute);
					backdrop-filter: blur(2px);
				}
			}
			&.zone {
				background-position: top center;
				background-size: cover;
			}
			&.has-image.is-not-expanded .title .button {
				background-color: var(--color-background);
			}
			&.new-location {
				background-color: var(--color-background);
			}
		}
	}
</style>
