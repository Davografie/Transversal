<script setup lang="ts">
	import { marked } from 'marked'
	import { ref, type Ref, watch, inject, computed, onMounted, nextTick } from 'vue'
	import { useRoute, useRouter } from 'vue-router'
	import { useFetch, useElementSize, useScroll } from '@vueuse/core'

	import { input_methods, usePlayerStore } from '@/stores/PlayerStore'
	// import { useCharacter } from '@/composables/Character'
	import { useEntity, entity_icons } from '@/composables/Entity'
	import { useLocation } from '@/composables/Location'
	// import { useTraitsetList } from '@/composables/TraitsetList'
	import type { Traitset as TraitsetType } from '@/interfaces/Types'
	import { ButtonTypes } from '@/composables/Button'

	import PlotPoint from '@/components/PlotPoint.vue'
	import Traitset from '@/components/Traitset.vue'
	// import AllTraits from '@/components/AllTraits.vue'
	import EntityButton from '@/components/EntityButton.vue'
	import ArchetypePicker from '@/components/ArchetypePicker.vue'
	import ButtonMinimal from '@/components/UI/ButtonMinimal.vue'

	import useClipboard from 'vue-clipboard3'
	const { toClipboard } = useClipboard()
	const copy_id = async () => {
		try {
			await toClipboard(entity.value.id)
		} catch (e) {
			console.error(e)
		}
	}

	const props = defineProps({
		entity_key: String,
		windowWidth: Number,	// used in styling
		orientation: {
			type: String,
			default: 'landscape',
		}
	})

	const emit = defineEmits(['show_entity'])

	const API_URL = inject('API_URL')
	const player = usePlayerStore()
	const router = useRouter()
	const route = useRoute()

	// variable to track long-press
	const held = ref(false)

	const {
		entity,
		set_entity_id,
		retrieve_small_entity,
		retrieve_full_entity,
		retrieve_instances,
		clone_entity,
		delete_entity,
		create_relation,
		prune_location,
		update_entity
	} = useEntity(player.the_entity?.key == props.entity_key ? player.the_entity : undefined, 'Entities/' + (props.entity_key ?? route.params.id))
	// retrieve_small_entity()

	function mutate_pp(delta: number) {
		update_entity({
			pp: (entity.value.pp ?? 0) + delta
		})
	}

	const {
		location,
		retrieve_small_location,
		retrieve_presence,
		set_location_key
	} = useLocation(undefined, entity.value?.location?.id)


	// entity name and type
	const new_name = ref('')
	const new_entityType = ref('character')
	const editing_name_type = ref(false)
	function longpress_name() {
		held.value = true
		editing_name_type.value = true
		setTimeout(() => held.value = false, 500)
	}
	function update_name_type() {
		update_entity({
			name: new_name.value,
			entityType: new_entityType.value
		})
		editing_name_type.value = false
	}


	const plot_points_element = ref(null)
	const plot_point_element = ref(null)
	const add_plot_point_element = ref(null)
	const { width: pp_width } = useElementSize(plot_point_element)
	const { width: add_pp_width } = useElementSize(add_plot_point_element)
	const showing_max_plot_points = computed<number>(() => {
		return (banner_width.value - add_pp_width.value) / (pp_width.value + 20)
	})

	function decrease_pp() {
		mutate_pp(-1)
	}

	function increase_pp() {
		mutate_pp(1)
	}


	// character description
	const new_description = ref('')
	const description = computed(() => {
		if(entity.value.description) {
			return marked(entity.value.description)
		}
		else {
			return ""
		}
	})
	const editing_description = ref(false)
	function longpress_description() {
		held.value = true
		editing_description.value = true
		setTimeout(() => held.value = false, 500)
	}
	function click_save() {
		editing_description.value = false
		update_entity({
			description: new_description.value,
			entityType: new_entityType.value
		})
	}


	// entity portrait
	// const portrait_image = ref(null)

	const file_upload: Ref<File | null> = ref(null)

	const portrait_updated = ref(false)
	const show_image = ref(false)

	const editing_portrait = ref(false)

	function longpress_portrait() {
		held.value = true
		editing_portrait.value = true
		setTimeout(() => held.value = false, 500)
	}

	function click_portrait() {
		if(!held.value && !editing_portrait.value) {
			show_image.value = true
		}
	}

	function cancel_portrait_edit() {
		editing_portrait.value = false
		file_upload.value = null
	}

	function handle_fileupload(event: any) {
		file_upload.value = event.target.files[0]
	}

	function submit_fileupload() {
		if(file_upload.value) {
			let url = API_URL + "upload/" + entity.value.key
			if(entity.value.location) url += "/" + entity.value.location.key
			console.log("uploading file: " + file_upload.value.name + " to url: " + url)
			const formData = new FormData()
			formData.append('file', file_upload.value)
			interface API_result {
				success: boolean
			}
			useFetch<API_result>(url, { method: 'POST', body: formData }).post().json()
			portrait_updated.value = true
			let temp_img = portrait_img.value
			portrait_img.value = null
			portrait_img.value = temp_img
		}
		editing_portrait.value = false
	}

	function imagen() {
		editing_portrait.value = false
		const url = API_URL + "imagen/" + entity.value.key + "/" + player.is_gm
		interface API_result {
			success: boolean
		}
		useFetch<API_result>(url, { method: 'POST' }).post().json()
		player.tickets_remaining -= 1
	}

	const img_link_small = computed(() => {
		if(entity.value.image) {
			return '/assets/uploads/' + entity.value.image.path
				+ '/small' + entity.value.image?.ext
		}
		else {
			return '/assets/uploads/' + entity.value.entityType + '/small.png'
		}
	})

	const img_link_large = computed(() => {
		if(entity.value.image) {
			return '/assets/uploads/' + entity.value.image.path
				+ '/large' + entity.value.image?.ext
		}
		else {
			return '/assets/uploads/' + entity.value.entityType + '/large.png'
		}
	})



	// used in css:
	const entity_wrapper = ref()
	const traitset_wrapper = ref()
	const character_wrapper = ref()

	const portrait_img = ref(null)
	const { width: portrait_width} = useElementSize(portrait_img)
	const { height: portraitHeight, width: portraitWidth } = useElementSize(portrait_img)
	const { width: entity_width } = useElementSize(entity_wrapper)

	// const { y: scrollY, directions: scrollDirections } = useScroll(character_wrapper)
	const { y: traitset_scrollY, directions: traitset_scrollDirections, arrivedState: traitset_arrived } = useScroll(traitset_wrapper)

	const detail_height = computed(() => portrait_img.value ? portraitHeight.value * 0.9 : 200)
	const character_wrapper_max_scroll_y = computed(() => character_wrapper.value ? character_wrapper.value.scrollHeight - character_wrapper.value.offsetHeight : 0)

	watch(traitset_scrollDirections, (newDirections) => {
		if(newDirections.top) {
			scrolling_up.value = true
		}
		else if(newDirections.bottom) {
			scrolling_up.value = false
		}
	})
	const scrolling_up = ref(false)
	// const scrolling_up = computed(() => {
	// 	return traitset_scrollDirections.top || traitset_arrived.top
	// })
	// const show_buttons =

	// const show_controls = computed(() => {
	// 	return traitset_arrived.top || traitset_scrollY.value < 100
	// })
	const show_controls = ref(false)
	const banner_width = computed(() => (props.windowWidth ?? entity_width.value) - portraitWidth.value)

	const min_banner_height = 100
	const max_banner_height = 240
	const banner_height = computed(() => {
		// uses entity.value.image.width and the traitset scroll Y to determine the banner height
		// at top of traitset scroll the banner is max size
		// scrolling down shrinks the banner height to min size, depending on scroll Y
		// where it remains until the user scrolled back up to the top
		if(player.input_method == input_methods.touch) return min_banner_height
		const scrollY_threshold = 100
		const scrollY_ratio = Math.min(1, traitset_scrollY.value / scrollY_threshold)
		const height = max_banner_height - (max_banner_height - min_banner_height) * scrollY_ratio
		return height
	})

	function reset_scroll() {
		traitset_scrollY.value = 0
	}

	function scroll_to_element(element_id: string) {
		console.log("scrolling to element: " + element_id)
		const element = document.getElementById(element_id)
		if(element) {
			console.log("element found, scrolling to it")
			element.scrollIntoView({ behavior: 'smooth', block: 'center' })
		}
		show_reference.value = false
	}

	function scroll_to_traitset(traitset: TraitsetType) {
		active_traitset_id.value = traitset.id
		const el_id = 'ts-' + traitset.name?.replace(' ', '-').toLowerCase() + '-' + entity.value.key
		console.log("scrolling to traitset: " + el_id)
		nextTick(() => scroll_to_element(el_id))
	}

	function set_traitset(set: TraitsetType) {
		// console.log('traitset: ', set)
		if(set) {
			// active_traitset_id.value = set.id
			scroll_to_traitset(set)
		}
	}

	watch(entity, (newCharacter) => {
		new_name.value = newCharacter.name
		new_description.value = newCharacter.description ?? ''
		new_entityType.value = newCharacter.entityType
	})

	watch(() => props.entity_key, (newKey) => {
		if(player.the_entity && player.the_entity?.key == newKey && !entity.value.key) {
			console.log('setting entity value from player store')
			entity.value = player.the_entity
		}
		if(newKey && entity.value.key != newKey) {
			console.log('setting entity key: ' + newKey)
			console.log('entity.value.key: ' + entity.value.key)
			console.log('player.the_entity.key: ' + player.the_entity?.key)
			set_entity_id('Entities/' + newKey)
			retrieve_full_entity()

			nextTick(() => character_wrapper.value?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
			switching_entities.value = false
		}
	})


	// watch(character, (newChar, oldChar) => {
	// 	if(newChar.id != oldChar.id && newChar.entityType == 'npc' && !newChar.isArchetype) {
	// 		console.log("gm perspective changed to npc: " + newChar.name + "/" + newChar.key)
	// 		player.set_perspective_id(newChar.id)
	// 		player.retrieve_perspective()
	// 	}
	// })



	watch(() => entity.value.id, () => {
		active_traitset_id.value = entity.value.traitsets && entity.value.traitsets.length > 0 ?
			entity.value.traitsets[0].id :
			''
		show_controls.value = false
	})

	// traits
	const active_traitset_id = ref(
		entity.value.traitsets && entity.value.traitsets.length > 0 ?
		entity.value.traitsets[0].id :
		''
	)


	// the GM's perspective changes location, so reflect that in the traits
	watch(() => player.the_entity?.location, (newLocation, oldLocation) => {
		if(player.the_entity?.id == entity.value.id && newLocation != oldLocation) {
			retrieve_small_entity()
		}
	})


	// character options
	function pick_character() {
		if(entity.value && entity.value.key != 'placeholder') {
			if(player.is_gm) {
				player.set_perspective_id(entity.value.id)
				player.retrieve_perspective()
			}
			else if(player.is_player) {
				player.player_character_key = entity.value.key
				// if(player.uuid) { activate_character(player.uuid) }
			}
		}
	}

	function switch_gm() {
		if(player.is_gm) {
			player.set_perspective_id('Entities/1')
			player.retrieve_perspective()
		}
	}

	const deletion = ref(false)
	function entity_deletion(rmtree?: boolean) {
		if(rmtree) {
			prune_location()
		}
		else {
			delete_entity()
		}
		deletion.value = false
		player.set_perspective_id('Entities/1')
		player.retrieve_perspective()
	}

	function relate() {
		if(player.the_entity) {
			create_relation(player.the_entity.id)
			setTimeout(() => player.is_gm ? player.retrieve_perspective_relations() : player.retrieve_relations(), 200)
		}
	}

	function hide_entity() {
		update_entity({ hidden: !entity.value.hidden })
	}

	const entityOverviewTypes = Object.freeze({
		NONE: 'none',
		KNOWN_TO: 'known_to',
		QUICK_SWITCH: 'quick_switch',
		ARCHETYPES: 'archetypes',
		INSTANCES: 'instances',
	})

	const entityOverviewType = ref<keyof typeof entityOverviewTypes>('NONE')

	function toggleEntityOverviewType(type: keyof typeof entityOverviewTypes) {
		entityOverviewType.value = type
	}

	const show_known_to = ref(false)
	function toggle_known_to() {
		if(entityOverviewType.value != 'KNOWN_TO' && entity.value.location?.key) {
			set_location_key(entity.value.location.key)
			retrieve_small_location()
			retrieve_presence()
			toggleEntityOverviewType('KNOWN_TO')
		}
		else {
			toggleEntityOverviewType('NONE')
		}
		// show_known_to.value = !show_known_to.value
	}
	function remove_known_to(entity_id: string) {
		update_entity({ knownTo: entity.value.knownTo?.filter(e => e.id != entity_id).map(e => e.id) ?? [] })
		// setTimeout(() => retrieve_small_entity(), 200)
	}

	function cycle_traitset_defaults(reverse = false) {
		const order = ['COLLAPSED', 'ACTIVE', 'EXPANDED']
		const index = order.indexOf(player.traitset_defaults)
		let nextIndex = (index + (reverse ? -1 : 1)) % order.length
		if(nextIndex < 0) { nextIndex = order.length - 1 }
		player.traitset_defaults = order[nextIndex]
	}

	onMounted(() => {
		if(route.name == 'Landing') {
			console.log('Welcome! Setting character key from cookie: ' + player.the_entity)
			set_entity_id(player.the_entity?.id ?? '')
			// watch(() => player.the_entity?.id, (newId) => {
			// 	// set_character_key(newKey ?? '')
			// 	set_entity_id(newId ?? '')
			// })
		}
		if(player.the_entity && !entity.value.id) {
			entity.value = player.the_entity
		}
		if(!entity.value.id || entity.value.key == 'placeholder') {
			retrieve_full_entity()
		}
		character_wrapper.value?.scrollIntoView({ behavior: 'smooth' })
		reset_scroll()
	})

	const switching_entities = ref(false)
	function switch_to_entity(entity_id: string) {
		if(player.is_gm) {
			player.set_perspective_id(entity_id)
			player.retrieve_perspective()
		}
		else if(player.is_player) {
			// player.player_character_key = entity_id.substring(9)
			// nextTick(() => {
			// 	player.retrieve_character()
			// })
			player.set_character_id(entity_id)
			player.retrieve_character()
		}
		// switching_entities.value = false
		entityOverviewType.value = 'NONE'
		editing_name_type.value = false
		editing_description.value = false
	}


	const instances_visible = ref(false)
	function show_instances() {
		if(entityOverviewType.value != 'INSTANCES') {
			retrieve_instances()
			toggleEntityOverviewType('INSTANCES')
		}
		else {
			toggleEntityOverviewType('NONE')
		}
	}
	function toggle_archetype() {
		update_entity({
			isArchetype: !entity.value.isArchetype
		})
	}
	function show_archetypes() {
		if(entityOverviewType.value != 'ARCHETYPES') {
			toggleEntityOverviewType('ARCHETYPES')
		}
		else {
			toggleEntityOverviewType('NONE')
		}
	}
	function toggle_quick_switch() {
		if(entityOverviewType.value != 'QUICK_SWITCH') {
			player.retrieve_player()
			toggleEntityOverviewType('QUICK_SWITCH')
		}
		else {
			toggleEntityOverviewType('NONE')
		}
	}

	function click_instance(entity_id: string) {
		emit('show_entity', entity_id)
	}

	function quick_switch(entity_id: string) {
		if(player.is_player) {
			switch_to_entity(entity_id)
		}
		else if(player.is_gm && player.orientation == 'horizontal') {
			emit('show_entity', entity_id)
		}
		else {
			switch_to_entity(entity_id)
		}
		entityOverviewType.value = 'NONE'
	}

	function click_archetype(archetype_id: string) {
		emit('show_entity', archetype_id)
		editing_description.value = false
	}

	const show_reference = ref(false)

	function next_traitset(_traitset: TraitsetType) {
		if(entity.value.traitsets) {
			active_traitset_id.value = entity.value.traitsets[entity.value.traitsets?.indexOf(_traitset) + 1]?.id
			scroll_to_traitset(entity.value.traitsets[entity.value.traitsets?.indexOf(_traitset) + 1])
		}
	}

	const filtered_traitsets = computed(() => {
		if(!entity.value.traitsets) { return [] }
		return entity.value.traitsets.filter(ts => player.is_gm ? true : ts.entityTypes ? !ts.entityTypes?.includes('gm') || ts.id == 'Traitsets/1' : true)
	})
</script>

<template>
	<div id="entity-wrapper" :class="[{ 'editing': player.editing }, props.orientation]" ref="entity_wrapper">
		<div id="portrait-lightbox" v-if="show_image" @click="show_image = false">
			<h1>{{ entity.name }}</h1>
			<img id="portrait_large" v-if="entity.image && show_image"
				:src="img_link_large" />
		</div>
		<div id="character-details">
			<div id="character-portrait">
				<img :src="img_link_small"
					v-touch:hold="longpress_portrait"
					@click.right="longpress_portrait"
					@click="click_portrait"
					@contextmenu="(e) => e.preventDefault()"
					ref="portrait_img" />
				<div id="portrait-upload-wrapper" v-if="editing_portrait">
					<div id="portrait-upload" class="portrait-edit-segment">
						<input type="file" id="file-upload" @change="handle_fileupload"
							v-show="false" />
						<label for="file-upload" id="file-upload-label" v-if="!portrait_updated">
							{{ file_upload ? file_upload.name : 'upload'}}
						</label>
						<input type="button" id="upload-file" class="button-mnml" value="upload"
							@click="submit_fileupload"
							v-if="file_upload && !portrait_updated" />
					</div>
					<div class="limiter" @click="cancel_portrait_edit">
						CANCEL
					</div>
					<div id="generate-portrait" class="portrait-edit-segment">
						<input type="button" class="button-mnml" id="generate-portrait-button" :value="'imagen (' + player.tickets_remaining + ')'"
							@click="imagen" v-if="!entity.imagened || player.is_gm" />
					</div>
				</div>
			</div>
			<div id="character-banner">
				<h1 v-touch:hold="longpress_name"
						@click.right="longpress_name"
						@contextmenu="(e) => e.preventDefault()"
						v-if="!editing_name_type">
					{{ entity.name }}
				</h1>
				<div id="entity-name-wrapper" :class="{ 'editing': editing_name_type }">
					<input type="text" id="entity-name" class="header" v-model="new_name" v-if="editing_name_type" />
					<select name="entity-type" id="entity-type" v-model="new_entityType" v-if="editing_name_type && player.is_gm">
						<option value="character">Character</option>
						<option value="npc">NPC</option>
						<option value="asset">Asset</option>
						<option value="faction">Faction</option>
						<option value="location">Location</option>
						<option value="gm">GM</option>
					</select>
					<input type="button" class="button" :value="player.small_buttons ? '💾' : '💾 save'"
						@click="update_name_type"
						v-if="(player.editing || editing_name_type) && (entity.name != new_name || entity.entityType != new_entityType)" />
					<input type="button" class="button" :value="player.small_buttons ? '✖' : '✖ cancel'"
						@click="editing_name_type = false" v-if="editing_name_type" />
				</div>
				<div id="plot_points" ref="plot_points_element">
					<PlotPoint ref="plot_point_element" class="plot_point" v-if="entity.pp"
						:amount="(entity.pp ?? 0) > showing_max_plot_points ? (entity.pp ?? 0) : undefined"
						@click="decrease_pp" />
					<PlotPoint class="plot_point"
						v-for="i in (entity.pp || 0) - 1" :key="i"
						v-if="(entity.pp ?? 0) > 0 && (entity.pp ?? 0) <= showing_max_plot_points"
						@click="decrease_pp" />
					<div ref="add_plot_point_element" id="add_pp" @click="increase_pp" class="button-mnml">
						<!-- <span>{{ player.small_buttons ? '+' : '+☯' }}</span> -->
						<!-- <img src="/img/icons/plot_point.png" class="icon" /> -->
						<span class="icon">+</span>
						<span class="label" v-if="!player.small_buttons">add plot point</span>
					</div>
				</div>

				<Transition name="fade-description">
					<div id="character-description" v-if="banner_height > min_banner_height">
						<div id="character-meta" v-if="player.is_gm">
							{{ entity.isArchetype ? 'archetype ' : '' }}
							{{ entity.entityType }} located in
							<span v-if="!entity.location || player.the_entity?.id == entity.id">{{ entity.location?.name }}</span>
							<a v-else @click="player.set_perspective_location(entity.location ?? entity.location)">{{ entity.location?.name }} ⬇</a>
							<div v-if="(player.editing || (player.is_gm && (editing_description || editing_name_type)))">
								instance of
								<EntityButton
									v-for="archetype in entity.archetypes"
									:entity_id="archetype.id"
									override_click
									@click_entity="click_archetype(archetype.id)"
									/>
								<input type="button" class="button-mnml" value="⬆" @click="switch_to_entity(entity.archetype.id)" v-if="player.is_gm && entity.archetype" />
							</div>
						</div>
						<div id="character-description-text"
							v-html="description"
							v-if="!editing_description"
							v-touch:hold="longpress_description"
							@click.right="longpress_description"
							@contextmenu="(e) => e.preventDefault()" />
						<textarea id="character-description-text"
							v-model="new_description"
							v-if="editing_description" />
					</div>
				</Transition>
				<input type="button" class="button" :value="'save ' + entity.entityType"
					@click="click_save"
					v-if="editing_description" />
				<input type="button" class="button" value="cancel"
					@click="editing_description = false"
					v-if="editing_description" />
			</div>
		</div>
		<div id="character" v-if="entity" ref="character_wrapper">
			<!-- <div id="character-details-spacer" /> -->
			<!-- <ToggleButton truthy="archetype" falsy="" :default="player.is_gm" @toggle="toggle_gm" /> -->
			<div id="character-buttons" :class="[player.small_buttons ? 'small-buttons' : 'verbose-buttons', scrolling_up ? 'scrolling-up' : 'scrolling-down']" v-show="show_controls">

				<ButtonMinimal
					:function="ButtonTypes.GM"
					@click="switch_gm"
					v-if="player.is_gm && player.the_entity?.id != 'Entities/1'" />

				<div class="button-mnml" id="copy-id"
					title="copy ID"
					v-if="player.is_gm"
					@click="copy_id">
					<!-- <div class="icon">#</div> -->
					<img src="/img/icons/char_copy_id.png" class="icon" />
					<div class="label" v-if="!player.small_buttons">copy ID</div>
				</div>
				<div class="button-mnml" id="pick-character"
					:title="'play as ' + entity.name"
					v-if="entity.id != player.the_entity?.id && (player.is_gm || (entity.entityType == 'character'))"
					@click="pick_character">
					<div class="icon">{{ entity_icons[entity.entityType] }}</div>
					<div class="label" v-if="!player.small_buttons">pick {{entity.entityType}}</div>
				</div>
				<div class="button-mnml" id="create-relation"
					title="create relation"
					v-if="entity.id != player.the_entity?.id && !player.the_entity?.relations?.map(e => e.toEntity.id).includes(entity.id)"
					@click="relate">
					<div class="icon">🤝</div>
					<div class="label" v-if="!player.small_buttons">create relation</div>
				</div>

				<!-- <div class="button-mnml" :class="{ 'active': entityOverviewType == 'QUICK_SWITCH' }" id="entity-switch"
					title="switch entity"
					v-if="player.previous_perspective_ids.filter(p => p != player.the_entity?.id).length > 0"
					@click="toggle_quick_switch">
					<div class="icon">🔁</div>
					<div class="label" v-if="!player.small_buttons">switch entity</div>
				</div> -->
				<ButtonMinimal
					:class="{ 'active': entityOverviewType == 'QUICK_SWITCH'}"
					:function="ButtonTypes.SWITCH"
					v-if="(player.player.entities?.length ?? 0) > 0"
					@click="toggle_quick_switch" />

				<div class="button-mnml" id="archetype"
					:title="entity.isArchetype ? 'unarchetype' : 'make archetype'"
					v-if="player.is_gm"
					@click="toggle_archetype">
					<div class="icon">{{ entity.isArchetype ? '◑' : '○' }}</div>
					<div class="label" v-if="!player.small_buttons">{{ entity.isArchetype ? 'unarchetype' : 'make archetype' }}</div>
				</div>
				<div class="button-mnml" :class="{ 'active': entityOverviewType == 'INSTANCES' }" id="show-instances"
					title="show instances"
					v-if="entity.isArchetype"
					@click="show_instances">
					<div class="icon">⊛</div>
					<div class="label" v-if="!player.small_buttons">{{ entityOverviewType == 'INSTANCES' ? 'hide' : 'show' }} instances</div>
				</div>

				<!-- <div class="button-mnml" :class="{ 'active': entityOverviewType == 'ARCHETYPES' }" id="show-archetypes"
					title="show archetypes"
					@click="show_archetypes">
					<div class="icon">⊛</div>
					<div class="label" v-if="!player.small_buttons">{{ entityOverviewType == 'ARCHETYPES' ? 'hide' : 'show' }} archetypes</div>
				</div> -->
				<ButtonMinimal
					:class="{ 'active': entityOverviewType == 'ARCHETYPES'}"
					:function="ButtonTypes.ADD_ARCHETYPE"
					@click="entityOverviewType == 'ARCHETYPES' ? entityOverviewType = 'NONE' : entityOverviewType = 'ARCHETYPES'" />

				<div class="button-mnml" id="clone-entity"
					title="clone entity"
					v-if="entity.isArchetype && player.is_gm"
					@click="clone_entity()">
					<div class="icon">⧉</div>
					<div class="label" v-if="!player.small_buttons">clone entity</div>
				</div>
				<div class="button-mnml" id="hide-entity"
					title="hide entity"
					v-if="player.is_gm && entity.entityType != 'character'"
					@click="hide_entity">
					<div class="icon">{{ entity.hidden ? '🌑' : '🌕' }}</div>
					<div class="label" v-if="!player.small_buttons">{{ entity.hidden ? 'hiding entity' : 'showing entity' }}</div>
				</div>
				<div class="button-mnml" :class="{ 'active': entityOverviewType == 'KNOWN_TO' }" id="show-known-to"
					title="show known to"
					v-if="player.is_gm && entity.knownTo && entity.knownTo.length > 0"
					@click="toggle_known_to">
					<div class="icon">👀</div>
					<div class="label" v-if="!player.small_buttons">known to</div>
				</div>
				<ButtonMinimal :function="ButtonTypes.KNOWN_TO"
					@click="toggle_known_to"
					v-if="player.is_gm && entity.knownTo && entity.knownTo.length > 0" />

				<ButtonMinimal :function="ButtonTypes.TRAITSET_CLOSED"
					@click="cycle_traitset_defaults(false)"
					@click.right.prevent="cycle_traitset_defaults(true)"
					v-if="player.traitset_defaults == 'COLLAPSED'" />
				<ButtonMinimal :function="ButtonTypes.TRAITSET_ACTIVE"
					@click="cycle_traitset_defaults(false)"
					@click.right.prevent="cycle_traitset_defaults(true)"
					v-else-if="player.traitset_defaults == 'ACTIVE'" />
				<ButtonMinimal :function="ButtonTypes.TRAITSET_OPEN"
					@click="cycle_traitset_defaults(false)"
					@click.right.prevent="cycle_traitset_defaults(true)"
					v-else-if="player.traitset_defaults == 'EXPANDED'" />

				<div class="button-mnml" id="delete-entity"
					title="delete entity"
					v-if="player.is_gm && entity.key != 'placeholder' && !['1', '2'].includes(entity.key) && deletion == false"
					@click="deletion = true">
					<!-- <div class="icon">🗑</div> -->
					<img src="/img/icons/trash.png" class="icon" />
					<div class="label" v-if="!player.small_buttons">delete entity</div>
				</div>
				<div id="delete-confirmation" v-if="deletion">
					<label>🗑</label>
					<div class="button-mnml verify-rmtree" id="verify-rmtree"
						title="delete recursively"
						v-if="entity.entityType == 'location'"
						@click="entity_deletion(true)">
						<div class="icon">✔</div>
						<div class="label">prune</div>
					</div>
					<div class="button-mnml verify" id="verify-delete"
						title="confirm and delete"
						@click="entity_deletion(false)">
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

				<ButtonMinimal
					:function="ButtonTypes.SETTINGS"
					@click="router.push({ path: '/location/' + player.the_entity?.location?.key + '/settings' })" />
			</div>

			<div id="character-quick-switch" class="character-menu" v-show="show_controls"
					v-if="entityOverviewType == 'QUICK_SWITCH' && player.player.entities && player.player.entities.length > 0">
				<EntityButton
					class="entity-card"
					v-for="entity_id in player.player.entities.map(e => e.id)" :key="entity_id"
					:entity_id="entity_id"
					override_click
					:is_active="player.the_entity?.id != entity_id"
					@click_entity="player.the_entity?.id != entity_id ? quick_switch(entity_id) : null" />
			</div>

			<ArchetypePicker class="character-menu" v-if="entityOverviewType == 'ARCHETYPES'" v-show="show_controls" :entity_id="entity.id" :entity_type="entity.entityType" :location_id="entity.location?.id" />

			<div id="character-known-to" class="character-menu" v-if="player.is_gm && entityOverviewType == 'KNOWN_TO' && entity.knownTo && entity.knownTo.length > 0" v-show="show_controls">
				<div class="info">
					<div class="header">known to</div>
					<div class="explainer">click to remove from known to</div>
				</div>
				<div class="entity-cards">
					<EntityButton v-for="entity in entity.knownTo" :key="entity.key"
						:entity_id="entity.id"
						override_click
						@click_entity="remove_known_to(entity.id)" />
				</div>
			</div>

			<div id="archetype-instances" class="character-menu" v-if="entity.isArchetype && entityOverviewType == 'INSTANCES'" v-show="show_controls">
				<EntityButton v-for="instance in entity.instances" :key="instance.key"
					:entity_id="instance.id"
					override_click
					@click_entity="click_instance(instance.id)" />
			</div>
			<div id="character-buttons-toggle" @click="show_controls = !show_controls">
				<span>{{ show_controls ? '🔼' : '🔽' }}</span>
				<span>{{ show_controls ? 'hide' : 'show' }} character controls</span>
				<span>{{ show_controls ? '🔼' : '🔽' }}</span>
			</div>
		</div>
		<div id="traitsets" ref="traitset_wrapper" v-if="entity.traitsets">
			<div class="top-scroll-space"></div>
			<Suspense>
				<Traitset
					v-for="set in filtered_traitsets"
					:key="set.id + entity.key"
					:traitset="set"
					:traitset_id="set.id"
					:entity_id="entity.id"
					:entity="entity"
					:limit="set.limit"
					:expanded="(
							(set.id == active_traitset_id && player.traitset_defaults == 'ACTIVE')
							|| player.traitset_defaults == 'EXPANDED'
						)"
					:extensible="player.orientation == 'vertical' && (player.is_gm || (player.is_player && player.player_character.id == entity.id))"
					visible
					:location_key="entity.location?.key"
					:active="set.id == active_traitset_id && player.traitset_defaults == 'ACTIVE'"
					:next="player.traitset_defaults == 'ACTIVE' && entity.traitsets?.indexOf(set) - 1 < entity.traitsets.length && entity.traitsets[entity.traitsets.indexOf(set) - 1]?.id == active_traitset_id"
					:location="false"
					:relationship="false"
					@next="next_traitset(set)"
					@set_traitset="set_traitset"
					@unset_traitset="active_traitset_id = ''" />
			</Suspense>
			<div class="bottom-scroll-space"></div>
		</div>
		<div id="floating-bottom">
			<div class="button-mnml" @click="traitset_wrapper.scrollTop = 0; show_reference = false" v-if="!traitset_arrived.top">
				<div class="icon">⤒</div>
				<div class="label" v-if="!player.small_buttons">to top</div>
			</div>
			<div class="reference" v-if="show_reference">
				<div class="scroll-item" v-for="traitset in entity.traitsets?.filter(ts => entity.traitsets?.map(t => t.id).includes(ts.id))">
					<a @click="scroll_to_traitset(traitset)">
						{{ traitset.name }}
					</a>
				</div>
			</div>
			<div class="button-mnml" @click="show_reference = !show_reference">
				<div class="icon">☰</div>
				<div class="label" v-if="!player.small_buttons">scroll to</div>
			</div>
		</div>
		<!-- <div id="all-traits-wrapper">
			<AllTraits v-if="entity.id" :entity_id="entity.id" />
		</div> -->
	</div>
</template>

<style scoped>
	#entity-wrapper {
		overflow: hidden;
		#character-details {
			display: flex;
			align-items: center;
			/* position: sticky;
			top: 0;
			z-index: 2; */
			#character-portrait {
				position: relative;
				text-align: center;
				min-height: 100px;
				/* width: fit-content; */
				/* min-width: 15%; */
				/* width: v-bind((portrait_width + 6) + 'px'); */
				img {
					display: block;
					/* width: 100%; */
					max-height: v-bind(banner_height + 'px');
				}
				#portrait-upload-wrapper {
					position: absolute;
					top: 0;
					height: 100%;
					min-height: 20px;
					max-height: 240px;
					max-width: 180px;
					width: 100%;
					display: flex;
					flex-direction: column;
					#portrait-upload {
						background-image: linear-gradient(to top, var(--color-background) 0, var(--color-background-mute) 10%, transparent 50%);
						width: 100%;
						#file-upload-label {
							background-color: var(--color-background-mute);
							height: 100%;
							width: 100%;
							display: flex;
							justify-content: center;
							align-items: center;
							cursor: pointer;
							font-size: 1.4em;
						}
						#upload-file {
							background-color: var(--color-highlight);
							color: var(--color-highlight-text);
							cursor: pointer;
							width: 100%;
							padding: .4em 0;
							font-size: 1.2em;
						}
					}
					.limiter {
						background-color: var(--color-background-mute);
						cursor: pointer;
						padding: .8em 0;
					}
					#generate-portrait {
						background-image: linear-gradient(to bottom, var(--color-background) 0, var(--color-background-mute) 10%, transparent 50%);
						#generate-portrait-button {
							background-color: var(--color-highlight-mute);
							color: var(--color-highlight-text);
							cursor: pointer;
							width: 100%;
							height: 100%;
							font-size: 1.4em;
						}
					}
					.portrait-edit-segment {
						flex-grow: 1;
						display: flex;
						justify-content: center;
						align-items: center;
					}
					#portrait-upload {
						display: flex;
						flex-direction: column;
					}
				}
			}
			#character-banner {
				overflow-x: hidden;
				overflow-y: scroll;
				flex-grow: 1;
				height: 100%;
				/* width: v-bind((entity_width - portrait_width - 6) + 'px'); */
				#plot_points {
					text-align: center;
					display: inline-flex;
					justify-content: space-between;
					gap: 10px;
					border-radius: 20px;
					/* border: 1px solid var(--color-border); */
					margin: 0 .4em;
					max-width: 100%;
					#add_pp {
						/* background-color: var(--color-background-mute); */
						padding: .4em .8em;
						border: none;
						margin: 0;
						display: flex;
						flex-direction: column;
						.icon {
							font-size: 1em;
						}
						span.label {
							font-size: .8em;
						}
					}
				}
				.fade-description-enter-to {
					opacity: 1;
				}
				.fade-description-enter-active {
					transition: opacity 1s ease;
				}
				.fade-description-enter-from, .fade-description-leave-to {
					opacity: 0;
				}
				#character-description {
					#character-meta, #character-description-text {
						padding-left: .6em;
					}
					#character-description-text {
						min-height: v-bind((detail_height * .5) + 'px');
						max-height: v-bind(detail_height + 'px');
						width: 100%;
						max-height: 200px;
						overflow-y: scroll;
					}
				}
			}
		}
		#character {
			/* flex-grow: 1; */
			position: relative;
			#character-buttons {
				/* position: absolute; */
				/* margin-top: .2em; */
				display: flex;
				/* flex-wrap: wrap; */
				width: 100%;
				/* position: sticky; */
				/* top: 0; */
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
				.button-mnml {
					text-align: center;
					flex-grow: 1;
					text-shadow: var(--text-shadow);
					text-wrap: wrap;
					font-size: 1.2em;
					&.active {
						background-color: var(--color-highlight);
						color: var(--color-highlight-text);
						text-shadow: none;
					}
				}
			}
			#entity-name-wrapper.editing {
				display: flex;
				#entity-name {
					flex-grow: 1;
					font-size: 1.2em;
				}
			}
			#character-quick-switch {
				padding: 1em;
				display: flex;
				justify-content: space-around;
				width: 100%;
				overflow-x: auto;
				.entity-card {
					width: 50px;
					height: 100px;
				}
			}
			#archetype-instances {
				display: flex;
				max-width: 100%;
				overflow-x: auto;
			}
			#character-known-to {
				.entity-cards {
					display: flex;
					justify-content: space-around;
					flex-wrap: wrap;
				}
			}
			#character-buttons-toggle {
				display: flex;
				justify-content: space-evenly;
				background-color: var(--color-background-mute);
				padding: .4em 0;
				height: 2.4em;
			}
		}
		#portrait-lightbox {
			position: fixed;
			top: 0;
			left: 0;
			width: 100vw;
			height: 100vh;
			background-color: var(--color-background-mute);
			z-index: 10;
			display: flex;
			justify-content: center;
			align-items: center;
			backdrop-filter: blur(5px);
			h1 {
				font-size: 20em;
				line-height: 1;
				position: absolute;
				top: 0;
				left: 0;
			}
			#portrait_large {
				position: absolute;
				max-width: 100vw;
				max-height: 100vh;
				border: 1em solid var(--color-text);
			}
		}
		#traitsets {
			border-bottom: 1px solid var(--color-border);
			flex-grow: 1;
		}
		.bottom-scroll-space {
			height: 100px;
			width: 100%;
		}
		#floating-bottom {
			position: fixed;
			bottom: 100px;
			left: 0;
			z-index: 5;
			.reference {
				max-height: calc(100vh - 200px - 2em);
				overflow-y: auto;
			}
			.button-mnml {
				background-color: var(--color-background);
				border: 1px solid var(--color-border);
				height: 2em;
			}
		}
	}
	.editing #character-portrait img {
		box-shadow: 0 0 10px var(--color-editing);
	}
</style>

<style>
	.touch {
		#character-buttons {
			overflow: scroll hidden;
		}
		#traitsets {
			align-items: start;
			justify-content: space-between;
			scroll-snap-type: x mandatory;
			scroll-behavior: smooth;
			flex-direction: row;
			/* flex-wrap: wrap; */
			/* scroll-padding-top: -4em; */
			/* padding: 1em;
			padding-top: 2.8em; */
			overflow-y: hidden;
			overflow-x: auto;
			padding-top: 2.4em;
			.traitset {
				width: 100%;
				height: 100%;
			}
		}
	}
	.kbm {
		#character-buttons {
			flex-wrap: wrap;
		}
		#traitsets {
			flex-grow: 1;
			overflow: auto;
			flex-direction: column;
			padding-top: 2em;
		}
	}
	.dark {
		#entity-wrapper {
			/* scroll-snap-type: y mandatory; */
			scroll-padding: 2em;
			display: flex;
			flex-direction: column;
			height: 100vh;
			/* backdrop-filter: blur(5px); */
			position: relative;
			#character-details {
				background-color: var(--color-background-mute);
				/* margin: 0 1em; */
				/* border-radius: 50px 30px 30px 50px; */
				max-height: 240px;
				/* height: v-bind(portraitHeight + 'px'); */
				scroll-snap-align: start;
				/* position: fixed; */
				/* top: 0; */
				/* z-index: 2; */
				height: v-bind(banner_height + 'px');
				/* transition: height 1s ease-in-out; */
				box-shadow: 0 0 10px var(--color-background);
				#character-portrait img {
					/* border-radius: 30px 0 0 30px; */
					/* border: 1px solid var(--color-background); */
					/* border-top: 3px solid var(--color-background); */
					/* margin: .4em; */
					max-height: v-bind(banner_height + 'px');
					/* transition: max-height 1s ease-in-out; */
				}
				#character-banner {
					/* text-shadow: #000 0px 0px 2px, #000 0px 0px 4px, #000 0px 0px 8px, #000 0px 0px 2px; */
					#plot_points {
						/* background-color: var(--color-background-mute); */
						color: var(--color-text);
						/* border: 1px solid var(--color-border); */
						#add_pp {
							color: var(--color-text);
							border: 1px solid var(--color-border);
						}
					}
				}
			}
			#character {
				/* overflow-y: auto; */
				/* height: calc(100vh - v-bind(detail_height) + 'px' - 4em); */
				/* margin-top: v-bind(portraitHeight + 'px'); */
				scroll-snap-type: y mandatory;
				height: 0;
				z-index: 5;
				/* height: 100px; */
				/* flex-grow: 1; */
				#character-buttons {
					scroll-snap-align: start;
					overflow-x: auto;
					backdrop-filter: blur(5px);
					&.scrolling-up {
						position: sticky;
						top: 0;
						z-index: 1;
					}
					.minimal-button {
						text-shadow: var(--text-shadow);
						/* box-shadow: inset 0 0 10px var(--color-background-mute); */
						/* border: 1px solid var(--color-border); */
						padding: .2em 1em;
					}
				}
				.character-menu {
					background-color: var(--color-background-mute);
					backdrop-filter: blur(5px);
				}
				&.horizontal {
					background-image: linear-gradient(to left, var(--color-background-mute) 0, transparent 20px, transparent 100%);
				}
			}
			#traitsets {
				/* border-top: 1px solid var(--color-background); */
				display: flex;
				gap: .8em;
				.top-scroll-space {
					/* scroll-snap-align: start; */
					/* height: 100px; */
					background-color: var(--color-background);
				}
				.bottom-scroll-space {
					scroll-snap-align: end;
				}
			}
		}
	}
	.light {
		#entity-wrapper {
			overflow-y: auto;
			height: 100vh;
			#character-details {
				padding: .4em;
				#character-portrait {
					/* padding: 1em; */
					img, #portrait-upload-wrapper {
						border: 3px double var(--color-text);
					}
					#portrait-upload-wrapper {
						top: 1em !important;
						width: calc(100% - 2em) !important;
					}
				}
			}
			#character {
				#character-buttons {
					/* flex-wrap: wrap; */
				}
			}
			#traitsets {
				border-top: 1px solid var(--color-border);
			}
		}
	}
	.landscape {
		#entity-wrapper {
			#character-details {
				#character-portrait {
					
				}
			}
			/* padding-top: 4em; */
			#traitsets {
				.traitset {
					min-width: 33vw;
				}
			}
		}
	}
	#mobile-container #charactersheet-container #entity-wrapper {
		padding-bottom: 3em;
		#traitsets {
			/* padding-bottom: 105px; */
			.traitset {
				min-width: 100vw;
			}
		}
	}
</style>
