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
		onUnmounted
	} from 'vue'
	import { useRoute } from 'vue-router'
	import { useElementBounding, useWindowSize } from '@vueuse/core'

	import { usePlayer } from '@/stores/Player'
	import { useDicepoolStore } from '@/stores/DicepoolStore'

	import Traitset from '@/components/Traitset.vue'
	import EntityCard from './EntityCard.vue'
	import NewEntityCard from './NewEntityCard.vue'
	import Location from '@/components/Location.vue'
	import LocationPresence from '@/components/LocationPresence.vue'
	import ActiveNPC from '@/components/ActiveNPC.vue'
	// const LocationItem = defineAsyncComponent(() => import('@/components/Location.vue'))

	import { useLocation } from '@/composables/Location'
	import { useEntityList } from '@/composables/EntityList'

	import type { Location as LocationType } from '@/interfaces/Types'

	const route = useRoute()
	const player = usePlayer()
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
		import_entity
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

	function longpress_location_header() {
		held.value = true
		new_flavortext.value = location.value.flavortext
		editing_location.value = !editing_location.value
		title_pulsate.value = true
		setTimeout(() => held.value = false, 500)
	}

	const show_location_image = ref(false)

	function click_title() {
		// if(!held.value) {
		// 	if(player.is_player) {
		// 		transverse(location.value)
		// 	}
		// 	else {
		// 		expanded.value = !expanded.value
		// 		if(expanded.value) {
		// 			retrieve_location()
		// 		}
		// 	}
		// }
		if(props.transversable) {
			transverse(location.value)
		}
		else {
			if(!show_location_image.value) {
				show_active.value = false
				overwrite_active.value = ""
				show_location_image.value = true
			}
			else {
				show_location_image.value = false
			}
		}
	}

	function click_zone(zone: LocationType) {
		transverse(zone)
	}

	function transverse(loc: LocationType) {
		console.log("transversing to " + loc.name)
		emit('transverse', loc)
	}

	const expanded = ref(props.level < (props.show_levels ?? 2))

	function polling() {
		if(
			polling_active.value
			&& expanded.value
			&& location.value.key != 'placeholder'
			&& player.the_entity?.location?.key == props.loc
		) {
			console.log("retrieving presence " + location.value.name)
			retrieve_presence()

			if(
				player.the_entity?.following &&
				!location.value.entities?.map(e => e.id).includes(player.the_entity?.following.id ?? '')
			) {
				player.is_player ? player.retrieve_character() : player.retrieve_perspective()
				console.log("changed player location during polling to " + player.the_entity?.location?.key)
				router.push({ path: '/location/' + player.the_entity?.location?.key })
			}

		}
		if(polling_active.value) setTimeout(polling, 10000)
	}

	const polling_active = ref(expanded.value)

	polling()

	watch(() => location.value.entities, (newVal, oldVal) => {
		if(
			newVal != oldVal
			&& player.the_entity?.location?.key == props.loc
			&& (
				!newVal?.map(e => e.id).includes(player.the_entity?.id ?? '')
				|| (player.the_entity?.following && !newVal?.map(e => e.id).includes(player.the_entity?.following.id ?? ''))
			)
		) {
			console.log("changing player location")
			player.is_player ? player.retrieve_character() : player.retrieve_perspective()
			console.log("presence changed from " + oldVal + " to " + newVal + ", changed player location to " + player.the_entity?.location?.key)
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
						!e.hidden
						|| e.knownTo?.map(kt => kt.id).includes(player.player_character?.id ?? '')
						|| e.active
					)
				)
				|| e.entityType == 'asset'
				|| e.entityType == 'faction'
			) && !(
				e.isArchetype && player.is_player
			)
		)
	})

	// show_active true shows the active NPC prominently
	const show_active = ref(true)
	const overwrite_active = ref<string>("")
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
			overwrite_active.value = ""
		}
	})
	watch(() => props.active_entity_id, (newId) => {
		overwrite_active.value = newId
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

	function add_to_codex() {
		if(the_entity.value) {
			add_location_relationship(the_entity.value.id)
			player.is_gm ? player.retrieve_perspective_relations() : player.retrieve_relations()
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
		setTimeout(() => retrieve_location(), 400)
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

	const the_entity = computed(() => {
		if(!player.is_gm && player.player_character) {
			return player.player_character
		}
		else if(player.is_gm && player.perspective) {
			return player.perspective
		}
	})

	const image_link = ref(
		'/assets/uploads/' + location.value.image?.path + '/' +
		(player.data_saving ? 'small' : 'large') +
		location.value.image?.ext)
	const image_link_small = ref(
		'/assets/uploads/' + location.value.image?.path +
		'/small' + location.value.image?.ext)
	const gradient = ref('100%')
	const show_small_image = ref(true)
	watch(expanded, (newExpanded) => {
		if(newExpanded) {
			gradient.value = '200%'
		}
		else {
			gradient.value = '100%'
		}
	})
	watch(location, (newLocation) => {
		if(newLocation.image) {
			image_link.value = '/assets/uploads/' + newLocation.image.path +
				'/' + (player.data_saving ? 'small' : 'large') +
				newLocation.image.ext
			image_link_small.value = '/assets/uploads/' + newLocation.image.path +
				'/small' + newLocation.image.ext
		}
	})

	function establish_route() {
		if(the_entity.value) {
			make_transversable(the_entity.value.id)
			setTimeout(() => player.retrieve_perspective_relations(), 200)
		}
	}

	const show_flavortext = ref(false)

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
		setTimeout(() => retrieve_small_location(), 200)
	}

	function switch_perspective(entity_id: string) {
		player.set_perspective_id(entity_id)
		player.retrieve_perspective()
	}

	onMounted(() => {
		if(expanded.value) {
			retrieve_location()
			console.log("mounted location " + location.value.name + "")
		}
		show_small_image.value = player.data_saving
	})

	onUnmounted(() => {
		console.log("unmounting location " + location.value.name + ", disabling polling")
		polling_active.value = false
	})

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
			props.parent_width ?? 0 * (location.value.image?.height ?? 0) / (location.value.image?.width ?? 1)
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
	// const { left: this_left, width: this_width } = useElementBounding(location_element)
	// const location_left = computed(() => {
	// 	return props.parent_left ?? this_left.value
	// })
	// const location_width = computed(() => {
	// 	return props.parent_width ?? this_width.value
	// })
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
					v-touch:hold="longpress_location_header"
					@click.right="longpress_location_header"
					@click="click_title"
					@contextmenu="(e) => e.preventDefault()"
					v-if="location">
				
				<component :is="'h' + (props.level + 2)" class="location-name"
						:class="{ 'text-pulsate': title_pulsate }"
						@animationend="title_pulsate = false">
					{{ location.name != 'placeholder' ? location.name : 'transversal' }}
				</component>

				<input type="button" class="button transverse-button corner-button"
					:value="player.small_buttons ? '⬇' : '⬇\ntransverse'"
					v-if="!is_current_location
						&& player.is_gm
						&& player.perspective
						&& the_entity?.id != location.id
						&& editing_location"
					@click.stop="transverse(location)" />

				<input type="button" class="button link-button corner-button"
					:value="player.small_buttons ? '🗺' : '🗺\ntake perspective'"
					@click.stop="switch_perspective(location.id)"
					v-if="player.is_gm && route.params.id != location.key && editing_location" />
				
				<input type="button" class="button codex-button corner-button"
					:value="player.small_buttons ? '🏷' : '🏷\nadd to contacts'"
					@click.stop="add_to_codex"
					v-if="the_entity
						&& the_entity.entityType != 'location'
						&& the_entity.id != location.id
						&& !the_entity.relations?.map(e => e.toEntity.id).some(id => id == location.id)
						&& editing_location
					" />

				<input type="button" class="button codex-button corner-button"
					:value="player.small_buttons ? '⤠' : '⤠\nmake transversable'"
					@click.stop="establish_route"
					v-if="the_entity
						&& the_entity.entityType == 'location'
						&& the_entity.id != location.id
						&& !the_entity.relations?.map(e => e.toEntity.id).some(id => id == location.id)
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

			</div>

			<div class="content" v-if="expanded">
				<div class="left">
					<div class="presence attribute" v-if="presence && presence.length > 0">
						<EntityCard
							class="entity-card"
							v-if="presence && presence.length > 1"
							v-for="entity in presence.slice(Math.ceil(presence.length / 2))"
							:key="entity.key"
							:entity_id="entity.id"
							options_direction="right"
							:show_name="false"
							override_click
							:is_active="entity.active"
							@click_entity="(active_npc == entity.id && overwrite_active == 'empty') || overwrite_active != entity.id ?
								overwrite_active = entity.id : overwrite_active = 'empty'" />
						<NewEntityCard
							:location_id="location.id"
							options_direction="right"
							v-if="player.is_gm" />
					</div>
				</div>
				<div class="center">
					<div class="active-npc-wrapper" v-if="show_active && (active_npc || overwrite_active) && overwrite_active != 'empty'">
						<ActiveNPC
							class="active-npc"
							:entity_id="overwrite_active ? overwrite_active : active_npc"
							@hide_entity="overwrite_active = 'empty'"
							@show_entity="(entity_key) => emit('show_entity', entity_key)" />
					</div>
					<div class="location-image-wrapper" v-if="show_location_image">
						<img class="location-image" :src="image_link" @click="show_location_image = false" />
					</div>
				</div>
				<div class="right">
					<div class="presence attribute" v-if="presence && presence.length > 0">
						<EntityCard
							class="entity-card"
							v-if="presence && presence.length > 0"
							v-for="entity in presence.slice(0, Math.ceil(presence.length / 2))"
							:key="entity.key"
							:entity_id="entity.id"
							options_direction="left"
							:show_name="false"
							override_click
							:is_active="entity.active"
							@click_entity="(active_npc == entity.id && overwrite_active == 'empty') || overwrite_active != entity.id ?
								overwrite_active = entity.id : overwrite_active = 'empty'" />
					</div>
				</div>
			</div>
			<div class="description attribute" v-if="player.is_gm && expanded">
				<div class="attribute-header header" @click="show_flavortext = !show_flavortext">
					<span>description</span>
					<div class="border-bottom"></div>
				</div>
				<div class="attribute-body"
						v-if="show_flavortext && (rendered_flavortext || new_flavortext)">
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
					<Traitset
						v-for="traitset in location.traitsets?.filter(ts => player.is_gm ? true : !ts.entityTypes?.includes('gm'))"
						:key="traitset.id"
						:traitset_id="traitset.id"
						:entity_id="location.id"
						:location_key="props.loc"
						:limit="traitset.limit"
						:expanded="!(player.editing || editing_traits)"
						:visible="(player.editing || editing_traits)"
						:hide_title="!(player.editing || editing_traits)"
						:extensible="(player.editing || editing_traits)"
						:location="true"
						:polling="player.the_entity?.location?.key == props.loc
							&& (
								traitset.id == 'Traitsets/3' // assets
								|| traitset.id == 'Traitsets/906502' // resources
							)"
						@refetch="retrieve_location"
					/>
				</div>
			</div>
			<div class="entities attribute" v-if="expanded">
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
							<EntityCard v-for="entity in entities.filter(e => e.entityType != 'location')"
								:key="entity.key"
								:entity_id="entity.id"
								override_click
								is_active
								@click_entity="import_ett(entity.id)" />
						</div>
					</div>
					<div class="neighboring">
						<LocationPresence class="parent-location" v-for="(neigbor_location, index) in location.parents?.slice(1, 4).reverse() ?? []"
								:key="neigbor_location.key"
								:location_key="neigbor_location.key"
								:search="import_search"
								:level="3 - index"
								@click_entity="import_ett" />
						<LocationPresence class="transversable-location" v-for="neigbor_location in location.transversables ?? []"
								:key="neigbor_location.key"
								:location_key="neigbor_location.key"
								:search="import_search"
								:level="0"
								@click_entity="import_ett" />
						<LocationPresence class="zone-location" v-for="neigbor_location in location.zones ?? []"
								:key="neigbor_location.key"
								:location_key="neigbor_location.key"
								:search="import_search"
								:level="-1"
								@click_entity="import_ett" />
					</div>
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
							@click="create_zone(newZone); retrieve_location(); newZone = ''" />
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
		.location-component-wrapper {
			width: 100%;
			.title {
				cursor: pointer;
				display: flex;
				flex-direction: column;
				.location-name {
					flex-grow: 2;
					font-size: 2em;
				}
				.button {
					z-index: 2;
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
		&.hidden {
			&.is-not-expanded {
				>.location-component-wrapper >.title .location-name {
					text-shadow: 0 0 3px var(--color-text);
					color: transparent;
				}
			}
			&.is-expanded {
				>.title .location-name {
					color: var(--color-disabled);
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
						height: 70px;
					}
				}
			}
			.center {
				flex-grow: 1;
				display: flex;
				flex-direction: column;
				overflow-x: hidden;
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
		.attribute {
			.attribute-header {
				text-align: center;
				position: relative;
				font-size: 1.2em;
				padding: .4em 0;
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
						gap: .4em;
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
		}
		.attribute {
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
						min-height: 300px;
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
				padding: 3%;
				&>.attribute-body {
					display: flex;
					flex-wrap: wrap;
					gap: 1em;
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
	}
	.location-component.no-image {
		background-color: var(--color-background-mute);
	}
	.location-component.is-not-expanded {
		margin: .2em;
		.title {
			position: relative;
			width: 100%;
			height: 100%;
			white-space: preline;
			line-height: 4em;
			padding: 4em 3em;
			.corner-button {
				display: flex;
				position: absolute;
				margin: 0;
				font-size: 1.2em;
			}
		}
	}
	.location-component.is-expanded {
		position: relative;
		&.player {
			min-height: 75vh;
		}
		/* border: 1px solid var(--color-background); */
		width: 100%;
		>.location-component-wrapper {
			>.title {
				padding: 1em 3em 0 3em;
				.corner-button {
					position: absolute;
					margin: 0;
					font-size: 1.2em;
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
				.hide-button {
					top: 5.5em;
					border-bottom: none;
					border-right: none;
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
	.location-component.new-location {
		justify-content: center;
		.new-zone {
			text-align: center;
			font-size: 1.2em;
			padding: 1em;
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
				>.location-component-wrapper {
					backdrop-filter: v-bind('filter');
				}
			}
			div.content div.center div.location-image-wrapper img {
				max-width: 100%;
				box-shadow: 0 0 10px var(--color-background);
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
				text-shadow: var(--text-shadow);
				.flavortext, .corner-button {
					color: var(--color-text);
				}
				.title .location-name, .corner-button {
					text-shadow: var(--color-background) 0px 0px 2px,
						var(--color-background) 0px 0px 4px,
						var(--color-background) 0px 0px 8px,
						var(--color-background) 0px 0px 2px;
				}
				.flavortext {
					text-shadow: var(--color-background) 0px 0px 4px,
						var(--color-background) 0px 0px 8px,
						var(--color-background) 0px 0px 16px,
						var(--color-background) 0px 0px 4px;
					box-shadow: inset 0 0 50px var(--color-background-mute);
					backdrop-filter: blur(20px);
				}
			}
			&.is-expanded {
				background-color: transparent;
				.entities {
					.drawer {
						box-shadow: inset 0 0 100px var(--color-background);
					}
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
