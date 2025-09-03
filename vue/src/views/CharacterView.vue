<script setup lang="ts">
	import { marked } from 'marked'
	import { ref, watch, inject, computed, onMounted, nextTick } from 'vue'
	import { RouterLink, useRoute, useRouter } from 'vue-router'
	import { useFetch, useElementSize } from '@vueuse/core'

	import { usePlayer } from '@/stores/Player'
	import { useCharacter } from '@/composables/Character'
	import { useEntity, entity_icons } from '@/composables/Entity'
	import { useLocation } from '@/composables/Location'
	
	import PP from '@/components/PP.vue'
	import Traitset from '@/components/Traitset.vue'
	import EntityCard from '@/components/EntityCard.vue'

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

	const API_URL = inject('API_URL')
	const player = usePlayer()
	const router = useRouter()
	const route = useRoute()

	// variable to track long-press
	const held = ref(false)

	const {
		character,
		set_character_key,
		activate_character,
		mutate_pp,
		update_character,
		clone_entity,
		delete_entity,
		toggle_archetype,
		retrieve_character
	} = useCharacter(undefined, props.entity_key ?? (route.name == 'Entity' ? String(route.params.id) : player.the_entity?.key))

	const {
		entity,
		set_entity_id,
		retrieve_small_entity,
		create_relation,
		update_entity
	} = useEntity(undefined, 'Entities/' + (props.entity_key ?? route.params.id))
	retrieve_small_entity()

	const {
		location,
		retrieve_small_location,
		retrieve_presence,
		set_location_key
	} = useLocation(undefined, character.value?.location?.id)


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
		update_character({
			name: new_name.value,
			type: new_entityType.value
		})
		editing_name_type.value = false
		setTimeout(() => retrieve_character(), 200)
	}


	function decrease_pp() {
		mutate_pp(-1)
	}

	function increase_pp() {
		mutate_pp(1)
	}


	// character description
	const new_description = ref('')
	const description = computed(() => {
		if(character.value.description) {
			return marked(character.value.description)
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
		update_character({
			description: new_description.value,
			type: new_entityType.value
		})
		retrieve_character()
	}


	// entity portrait
	const file_upload = ref()
	const portrait_img = ref(null)

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
	}

	function handle_fileupload(event: any) {
		file_upload.value = event.target.files[0]
	}

	function submit_fileupload() {
		if(file_upload.value) {
			console.log("uploading file: " + file_upload.value.name)
			let url = API_URL + "upload/" + character.value.key
			if(character.value.location) url += "/" + character.value.location.key
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
		const url = API_URL + "imagen/" + character.value.key + "/" + player.is_gm
		interface API_result {
			success: boolean
		}
		useFetch<API_result>(url, { method: 'POST' }).post().json()
	}

	const img_link_small = computed(() => {
		if(character.value.image) {
			return '/assets/uploads/' + character.value.image.path
				+ '/small' + character.value.image?.ext
		}
		else {
			return '/assets/uploads/' + character.value.entityType + '/small.png'
		}
	})

	const img_link_large = computed(() => {
		if(character.value.image) {
			return '/assets/uploads/' + character.value.image.path
				+ '/large' + character.value.image?.ext
		}
		else {
			return '/assets/uploads/' + character.value.entityType + '/large.png'
		}
	})



	// used in css:
	const { height: portraitHeight, width: portraitWidth } = useElementSize(portrait_img)
	const detail_height = computed(() => portrait_img.value ? portraitHeight.value * 0.9 : 200)
	const entity_wrapper = ref()
	const character_wrapper = ref()
	const { width: entity_width } = useElementSize(entity_wrapper)
	const banner_width = computed(() => (props.windowWidth ?? entity_width.value) - portraitWidth.value)


	watch(character, (newCharacter) => {
		new_name.value = newCharacter.name
		new_description.value = newCharacter.description ?? ''
		new_entityType.value = newCharacter.entityType
	})

	watch(() => props.entity_key, (newKey) => {
		if(newKey && (character.value.key != newKey || entity.value.key != newKey)) {
			set_character_key(newKey)
			retrieve_character()
			retrieve_small_entity()

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



	watch(() => character.value.id, () => {
		active_traitset_id.value = character.value.traitsets && character.value.traitsets.length > 0 ?
			character.value.traitsets[0].id :
			''
	})

	// traits
	const active_traitset_id = ref(
		character.value.traitsets && character.value.traitsets.length > 0 ?
		character.value.traitsets[0].id :
		''
	)


	// the GM's perspective changes location, so reflect that in the traits
	watch(() => player.perspective.location, (newLocation, oldLocation) => {
		if(player.is_gm && player.perspective.id == character.value.id && newLocation != oldLocation) {
			retrieve_character()
		}
	})

	// the player's character changes location, so reflect that in the traits
	watch(() => player.player_character.location, (newLocation, oldLocation) => {
		if(!player.is_gm && player.player_character.id == character.value.id && newLocation != oldLocation) {
			retrieve_character()
		}
	})


	// character options
	function pick_character() {
		if(character.value && character.value.key != 'placeholder') {
			if(player.is_gm) {
				player.set_perspective_id(character.value.id)
				player.retrieve_perspective()
			}
			else if(player.is_player) {
				player.player_character_key = character.value.key
				if(player.uuid) { activate_character(player.uuid) }
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
	function entity_deletion() {
		delete_entity()
		router.push({ name: 'Character overview' })
	}

	function relate() {
		if(player.the_entity) {
			create_relation(player.the_entity.id)
			setTimeout(() => player.is_gm ? player.retrieve_perspective_relations() : player.retrieve_relations(), 200)
		}
	}

	function hide_entity() {
		update_entity({ hidden: !character.value.hidden })
		setTimeout(() => retrieve_character(), 200)
	}

	const show_known_to = ref(false)
	function toggle_known_to() {
		if(!show_known_to.value && character.value.location?.key) {
			set_location_key(character.value.location.key)
			retrieve_small_location()
			retrieve_presence()
		}
		show_known_to.value = !show_known_to.value
	}
	function remove_known_to(entity_id: string) {
		update_entity({ knownTo: entity.value.knownTo?.filter(e => e.id != entity_id).map(e => e.id) ?? [] })
		setTimeout(() => retrieve_small_entity(), 200)
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
			watch(() => player.the_entity?.key, (newKey) => {
				console.log('Welcome! Setting character key from cookie: ' + player.the_entity)
				set_character_key(newKey ?? '')
			})
		}
		character_wrapper.value?.scrollIntoView({ behavior: 'smooth' })
		// if(player.is_gm) {
		// 	watch(character, () => {
		// 		if(player.perspective_id != character.value.id && character.value.entityType == 'npc') {
		// 			player.perspective_id = character.value.id
		// 		}
		// 	}, { once: true })
		// }
	})

	const switching_entities = ref(false)
	function switch_to_entity(entity_id: string) {
		if(player.is_gm) {
			player.set_perspective_id(entity_id)
			player.retrieve_perspective()
		}
		else if(player.is_player) {
			player.player_character_key = entity_id.substring(9)
			if(player.uuid) { activate_character(player.uuid) }
		}
	}
</script>

<template>
	<div id="entity-wrapper" :class="[{ 'editing': player.editing }, props.orientation]" ref="entity_wrapper">
		<div id="portrait-lightbox" v-if="show_image" @click="show_image = false">
			<img id="portrait_large" v-if="character.image && show_image"
				:src="img_link_large" />
		</div>
		<div id="character-quick-switch" v-if="switching_entities && player.previous_perspective_ids.filter(p => p != player.the_entity?.id).length > 0">
			<EntityCard
				class="entity-card"
				v-for="entity_id in player.previous_perspective_ids" :key="entity_id"
				:entity_id="entity_id"
				override_click
				@click_entity="switch_to_entity(entity_id)" />
		</div>
		<div id="character" v-if="character" ref="character_wrapper">
			<!-- <ToggleButton truthy="archetype" falsy="" :default="player.is_gm" @toggle="toggle_gm" /> -->
			<div id="entity-name-wrapper" :class="{ 'editing': editing_name_type }">
				<input type="text" id="entity-name" class="header" v-model="new_name" v-if="editing_name_type" />
				<select name="entity-type" id="entity-type" v-model="new_entityType" v-if="editing_name_type && player.is_gm">
					<option value="character">Character</option>
					<option value="npc">NPC</option>
					<option value="asset">Asset</option>
					<option value="faction">Faction</option>
				</select>
				<input type="button" class="button" :value="player.small_buttons ? '💾' : '💾 save'"
					@click="update_name_type"
					v-if="(player.editing || editing_name_type) && (character.name != new_name || character.entityType != new_entityType)" />
				<input type="button" class="button" :value="player.small_buttons ? '✖' : '✖ cancel'"
					@click="editing_name_type = false" v-if="editing_name_type" />
			</div>
			<div id="character-details">
				<div id="character-portrait" ref="portrait_img">
					<img :src="img_link_small"
						v-touch:hold="longpress_portrait"
						@click.right="longpress_portrait"
						@click="click_portrait"
						@contextmenu="(e) => e.preventDefault()" />
					<div id="portrait-upload-wrapper" v-if="editing_portrait">
						<div id="portrait-upload" class="portrait-edit-segment">
							<input type="file" id="file" @change="handle_fileupload"
								v-if="!portrait_updated" />
							<input type="button" id="fileupload" class="button" value="upload"
								@click="submit_fileupload"
								v-if="file_upload && !portrait_updated" />
						</div>
						<div class="limiter" @click="cancel_portrait_edit">
							CANCEL
						</div>
						<div id="generate-portrait" class="portrait-edit-segment">
							<input type="button" class="button" value="generate!"
								@click="imagen" v-if="!character.imagened || player.is_gm" />
						</div>
					</div>
				</div>
				<div id="character-banner">
					<h1 v-touch:hold="longpress_name"
							@click.right="longpress_name"
							@contextmenu="(e) => e.preventDefault()"
							v-if="!editing_name_type">
						{{ character.name }}
						<input id="entity-switch" v-if="player.previous_perspective_ids.filter(p => p != player.the_entity?.id).length > 0"
							type="button" class="button-mnml" value="🔁" @click="switching_entities = !switching_entities" />
					</h1>
					<div id="plot_points">
						<PP class="plot_point" v-for="i in character.pp" v-if="character.pp && character.pp <= 5" :key="i" @click="decrease_pp" />
						<PP class="plot_point" v-else-if="character.pp" :amount="character.pp" @click="decrease_pp" />
						<div id="add_pp" @click="increase_pp">
							<span>{{ player.small_buttons ? '+' : '+☯' }}</span>
							<span class="label" v-if="!player.small_buttons">add plot point</span>
						</div>
					</div>

					<div id="character-description">
						<div id="character-meta" v-if="player.is_gm">
							{{ character.isArchetype ? 'archetype ' : '' }}
							{{ character.entityType }} located in
							<span v-if="!character.location || player.the_entity?.id == character.id">{{ character.location?.name }}</span>
							<a v-else @click="player.set_perspective_location(character.location)">{{ character.location?.name }} ⬇</a>
							<div v-if="character.archetype && (player.editing || (player.is_gm && (editing_description || editing_name_type)))">
								instance of 
								<RouterLink :to="'/Entity/' + character.archetype.key">
									{{ character.archetype.name }}
								</RouterLink>
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
					<input type="button" class="button" :value="'save ' + character.entityType"
						@click="click_save"
						v-if="editing_description" />
					<input type="button" class="button" value="cancel"
						@click="editing_description = false"
						v-if="editing_description" />
				</div>
			</div>
			<div id="character-buttons" :class="player.small_buttons ? 'small-buttons' : 'verbose-buttons'">
				<input type="button" class="button-mnml" id="switch-gm"
					:value="player.small_buttons ? entity_icons['gm'] : entity_icons['gm'] + '\nswitch to gm'"
					v-if="player.is_gm && player.the_entity?.id != 'Entities/1'"
					@click="switch_gm" />
				<input type="button" class="button-mnml" id="copy-id"
					:value="player.small_buttons ? '#' : '#\ncopy ID'"
					v-if="player.is_gm"
					@click="copy_id" />
				<input type="button" class="button-mnml" id="pick-character"
					:value="player.small_buttons ? entity_icons[character.entityType] : entity_icons[character.entityType] + '\npick ' + character.entityType"
					v-if="character.id != player.the_entity?.id && (player.is_gm || (character.entityType == 'character'))"
					@click="pick_character" />
				<input type="button" class="button-mnml" id="create-relation"
					:value="player.small_buttons ? '🤝' : '🤝\ncreate relation'"
					v-if="character.id != player.the_entity?.id && !player.the_entity?.relations?.map(e => e.toEntity.id).includes(character.id)"
					@click="relate" />
				<input type="button" class="button-mnml" id="archetype"
					:value="character.isArchetype ? (player.small_buttons ? '◑' : '◑\nunarchetype') : (player.small_buttons ? '○' : '○\nmake archetype')"
					:title="character.isArchetype ? 'unarchetype' : 'make archetype'"
					v-if="player.is_gm"
					@click="toggle_archetype" />
				<input type="button" class="button-mnml" id="clone-entity"
					:value="player.small_buttons ? '⧉' : 'clone entity ⧉'"
					title="clone entity"
					v-if="character.isArchetype && player.is_gm"
					@click="clone_entity" />
				<input type="button" class="button-mnml" id="hide-entity"
					:value="character.hidden ? (player.small_buttons ? '🌑' : '🌑\nhiding entity') : player.small_buttons ? '🌕' : '🌕\nshowing entity'"
					title="hide entity"
					v-if="player.is_gm && character.entityType != 'character'"
					@click="hide_entity" />
				<input type="button" class="button-mnml" id="show-known-to"
					:value="player.small_buttons ? '👀' : '👀\nknown to'"
					title="show known to"
					v-if="player.is_gm && entity.knownTo && entity.knownTo.length > 0"
					@click="toggle_known_to" />
				<input type="button" class="button-mnml" id="collapse-all-traitsets"
					:value="(function() {
						switch (player.traitset_defaults) {
							case 'COLLAPSED':
								return player.small_buttons ? '📕' : '📕\ncollapsed';
							case 'ACTIVE':
								return player.small_buttons ? '📑' : '📑\nactive';
							case 'EXPANDED':
								return player.small_buttons ? '📖' : '📖\nexpanded';
							default:
								return '';
						}
					})()"
					title="collapse all traitsets"
					@click="cycle_traitset_defaults(false)"
					@click.right.prevent="cycle_traitset_defaults(true)" />
				<input type="button" class="button-mnml" id="delete-entity"
					:value="player.small_buttons ? '🗑' : '🗑\ndelete entity'"
					title="delete entity"
					v-if="
						player.is_gm
						&& deletion == false
						&& character.key != 'placeholder'
						&& !['1', '2'].includes(character.key)"
					@click="deletion = true" />
				<input type="button" class="button-mnml" id="verify-delete"
					value="yes" title="confirm and delete"
					v-if="deletion" @click="entity_deletion" />
				<input type="button" class="button-mnml" id="cancel-delete"
					value="no" title="cancel deletion"
					v-if="deletion" @click="deletion = false" />
				<input type="button" class="button-mnml" :value="player.small_buttons ? '⚙' : '⚙\nsettings'"
					@click="router.push({ path: '/location/' + player.the_entity?.location?.key + '/settings' })"
					v-if="props.orientation == 'horizontal'" />
			</div>
			<div id="character-known-to" v-if="player.is_gm && show_known_to && entity.knownTo && entity.knownTo.length > 0">
				<div class="info">
					<div class="header">known to</div>
					<div class="explainer">click to remove from known to</div>
				</div>
				<div class="entity-cards">
					<EntityCard v-for="entity in entity.knownTo" :key="entity.key"
						:entity_id="entity.id"
						override_click
						@click_entity="remove_known_to(entity.id)" />
				</div>
			</div>
		</div>
		<div id="traitsets" v-if="character.traitsets">
			<Traitset
				v-for="set in character.traitsets.filter(ts => player.is_gm ? true : ts.entityTypes ? !ts.entityTypes?.includes('gm') || ts.id == 'Traitsets/1' : true)"
				:key="set.id + character.key"
				:traitset_id="set.id"
				:entity_id="character.id"
				:limit="set.limit"
				:expanded="((set.id == active_traitset_id && player.traitset_defaults == 'ACTIVE') || player.traitset_defaults == 'EXPANDED') && player.traitset_defaults != 'COLLAPSED'"
				:extensible="player.orientation == 'vertical' && (player.is_gm || (player.is_player && player.player_character.id == character.id))"
				visible
				:location_key="character.location?.key"
				:active="player.orientation == 'vertical' && set.id == active_traitset_id"
				:next="player.orientation == 'vertical' && character.traitsets?.indexOf(set) - 1 < character.traitsets.length && character.traitsets[character.traitsets.indexOf(set) - 1]?.id == active_traitset_id"
				:location="false"
				:relationship="false"
				@next="active_traitset_id = character.traitsets[character.traitsets?.indexOf(set) + 1]?.id"
				@set_traitset="active_traitset_id = set.id"
				@unset_traitset="active_traitset_id = ''" />
		</div>
		<div class="bottom-scroll-space"></div>
	</div>
</template>

<style scoped>
	#entity-wrapper {
		#character-quick-switch {
			padding: 1em;
			display: flex;
			justify-content: space-around;
			width: 100%;
			overflow-x: auto;
			.entity-card {
				width: 50px;
				height: 70px;
			}
		}
		#character {
			position: relative;
			#entity-name-wrapper.editing {
				display: flex;
				#entity-name {
					flex-grow: 1;
					font-size: 1.2em;
				}
			}
			#character-details {
				display: flex;
				align-items: center;
				#character-banner {
					overflow: scroll;
					flex-grow: 1;
					height: 100%;
					#plot_points {
						text-align: center;
						display: inline-flex;
						justify-content: space-between;
						border-radius: 20px;
						border: 1px solid var(--color-border);
						margin-left: 1em;
						#add_pp {
							/* background-color: var(--color-background-mute); */
							padding: .4em .8em;
							border: none;
							margin: 0;
							display: flex;
							flex-direction: column;
							span.label {
								font-size: .8em;
							}
						}
					}
					#character-description {
						#character-meta, #character-description-text {
							padding-left: .4em;
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
				#character-portrait {
					position: relative;
					text-align: center;
					min-height: 100px;
					width: fit-content;
					img {
						display: block;
						width: 100%;
						max-height: 240px;
					}
					#portrait-upload-wrapper {
						position: absolute;
						top: 0;
						height: 100%;
						min-height: 20px;
						max-width: 180px;
						display: flex;
						flex-direction: column;
						#portrait-upload {
							background-image: linear-gradient(to top, var(--color-background) 0, var(--color-background-mute) 10%, transparent 50%);
							#file {
								background-color: var(--color-background-mute);
							}
						}
						.limiter {
							background-color: var(--color-background-mute);
							cursor: pointer;
						}
						#generate-portrait {
							background-image: linear-gradient(to bottom, var(--color-background) 0, var(--color-background-mute) 10%, transparent 50%);
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
			}
			#character-known-to {
				.entity-cards {
					display: flex;
					justify-content: space-around;
					flex-wrap: wrap;
				}
			}
			#character-buttons {
				/* position: absolute; */
				/* margin-top: .2em; */
				display: flex;
				flex-wrap: wrap;
				width: 100%;
				.button-mnml {
					text-align: center;
					flex-grow: 1;
					text-shadow: var(--text-shadow);
					text-wrap: wrap;
					font-size: 1.2em;
				}
			}
		}
		#portrait-lightbox {
			position: fixed;
			top: 0;
			left: 0;
			width: 100vw;
			height: 100vh;
			background-color: var(--color-background-mute);
			z-index: 5;
			display: flex;
			align-items: center;
		}
		#portrait_large {
			max-width: 100vw;
			max-height: 100vh;
		}
		#traitsets {
			border-bottom: 1px solid var(--color-border);
		}
		.bottom-scroll-space {
			height: 100px;
		}
	}
	.editing #character-portrait img {
		box-shadow: 0 0 10px var(--color-editing);
	}
</style>

<style>
	.dark {
		#entity-wrapper {
			/* backdrop-filter: blur(5px); */
			#character-details {
				background-color: var(--color-background-mute);
				/* margin: 0 1em; */
				/* border-radius: 50px 30px 30px 50px; */
				max-height: 240px;
				height: v-bind(portraitHeight + 'px');
				#character-portrait img {
					/* border-radius: 30px 0 0 30px; */
					border: 1px solid var(--color-background);
					border-top: 3px solid var(--color-background);
					/* margin: .4em; */
				}
				#character-banner {
					/* text-shadow: #000 0px 0px 2px, #000 0px 0px 4px, #000 0px 0px 8px, #000 0px 0px 2px; */
					#plot_points {
						background-color: var(--color-background-mute);
						color: var(--color-text);
						border: 1px solid var(--color-border);
						#add_pp {
							color: var(--color-text);
							border: 1px solid var(--color-border);
						}
					}
				}
			}
			#character-buttons {
				.button-mnml {
					text-shadow: var(--text-shadow);
					backdrop-filter: blur(5px);
					box-shadow: inset 0 0 10px var(--color-background-mute);
					border: 1px solid var(--color-border);
					padding: .2em 1em;
				}
			}
			#traitsets {
				/* border-top: 1px solid var(--color-background); */
				display: flex;
				flex-wrap: wrap;
				align-items: start;
				justify-content: space-between;
				gap: 2em;
				padding: 1em;
			}
			&.horizontal {
				background-image: linear-gradient(to left, var(--color-background-mute) 0, transparent 20px, transparent 100%);
			}
		}
	}
	.light {
		#entity-wrapper {
			#character-details {
				padding: 0 .4em;
			}
			#character-portrait img {
				border: 3px double var(--color-text);
				margin: 1em;
			}
			#traitsets {
				border-top: 1px solid var(--color-border);
			}
		}
	}
	/* .landscape {
		#entity-wrapper {
			padding-top: 4em;
		}
	} */
</style>
