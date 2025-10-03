<script setup lang="ts">
	import { ref, computed, defineAsyncComponent } from 'vue'
	import type { Ref } from 'vue'
	import { useRouter } from 'vue-router'

	const router = useRouter()

	import { usePlayer } from '@/stores/Player'
	const player = usePlayer()

	const EntityCard = defineAsyncComponent(() => import('@/components/EntityCard.vue'))
	import NewEntityCard from '@/components/NewEntityCard.vue'
	import ToggleButton from '@/components/UI/ToggleButton.vue'
	import { useEntityList } from '@/composables/EntityList'
	import type { Entity as EntityType } from '@/interfaces/Types'

	const emit = defineEmits(['show_entity'])

	const {
		entities,
		retrieve_entities,
		create_entity,
		entityType
	} = useEntityList(undefined, 'character')
	retrieve_entities()

	const new_entity_name: Ref<string> = ref("")
	const new_entityType: Ref<string> = ref("character")
	
	const show_characters = ref<boolean>(!player.is_gm)
	const show_npcs = ref<boolean>(false)
	const show_factions = ref<boolean>(false)
	const show_assets = ref<boolean>(false)
	const show_character_creation = ref<boolean>(false)

	async function create_character(name: string, entityType: string) {
		const new_entity = await create_entity(name, entityType)
		router.push({ path: '/entity/' + new_entity.key })
	}

	function switch_character(entity: EntityType) {
		if(player.is_gm) {
			player.set_perspective_id(entity.id)
			player.retrieve_perspective()
		}
		else if(player.is_player) {
			player.player_character_key = entity.key
		}
	}

	function display_characters() {
		if(!show_characters.value) {
			entityType.value = 'character'
			retrieve_entities()
			show_characters.value = true
			show_npcs.value = false
			show_factions.value = false
			show_assets.value = false
		}
		else {
			show_characters.value = false
		}
	}

	function display_npcs() {
		if(!show_npcs.value) {
			entityType.value = 'npc'
			retrieve_entities()
			show_characters.value = false
			show_npcs.value = true
			show_factions.value = false
			show_assets.value = false
		}
		else {
			show_npcs.value = false
		}
	}

	function display_factions() {
		if(!show_factions.value) {
			entityType.value = 'faction'
			retrieve_entities()
			show_characters.value = false
			show_npcs.value = false
			show_factions.value = true
			show_assets.value = false
		}
		else {
			show_factions.value = false
		}
	}

	function display_assets() {
		if(!show_assets.value) {
			entityType.value = 'asset'
			retrieve_entities()
			show_characters.value = false
			show_npcs.value = false
			show_factions.value = false
			show_assets.value = true
		}
		else {
			show_assets.value = false
		}
	}

	const search = ref("")

	const show_archetypes = ref(false)
</script>

<template>
	<div id="character-overview-wrapper">
		<div id="favorites" v-if="player.is_gm && entities.filter((e) => e.favorite).length > 0">
			<h1>favorites</h1>
			<div class="entities">
				<EntityCard v-for="entity in entities.filter((e) => e.favorite)" :key="entity.key"
					:entity_id="entity.id" @refresh_favorites="retrieve_entities" />
			</div>
		</div>
		<div id="search">
			<input type="text" placeholder="search" v-model="search" />
		</div>
		<div id="filters">
			<ToggleButton
				truthy="show archetypes" falsy="hide archetypes"
				:default="show_archetypes" @toggle="show_archetypes = !show_archetypes"
				v-if="player.is_gm" />
		</div>
		<div id="characters">
			<h1 @click="display_characters">characters</h1>
			<div class="entities" v-show="show_characters">
				<NewEntityCard
					location_id="Entities/1"
					entity_type="character"
					archetype_id="Entities/3"
					options_direction="inside" />
				<EntityCard
					v-for="entity in entities.filter((e) => e.entityType == 'character'
						&& e.name.toLowerCase().indexOf(search.trim().toLowerCase()) != -1
						&& (
							(player.is_player && !e.isArchetype)
							|| (player.is_gm && (!show_archetypes && !e.isArchetype) || (show_archetypes && e.isArchetype))
						))"
					:key="entity.key"
					:entity_id="entity.id"
					@refresh_favorites="retrieve_entities"
					show_unavailable
					:is_active="!entity.active"
					override_click
					@click_entity="switch_character(entity)" />
			</div>
		</div>
		<h1 v-if="player.is_gm" @click="display_npcs" :class="[{ 'current': show_npcs }, { 'next': show_characters }]">npcs</h1>
		<div id="npcs" v-if="player.is_gm">
			<div class="entities" v-if="show_npcs">
				<div class="entity-card no-image">
					<div class="card-wrapper clicker" v-if="!show_character_creation" @click="new_entityType = 'npc'; show_character_creation = true">
						+
					</div>
					<div class="card-wrapper" v-else>
						<input type="text" :placeholder="'add ' + new_entityType" v-model="new_entity_name" />
						<input type="button" class="button"
							:value="new_entity_name ? 'add' : 'cancel'"
							@click="new_entity_name ? create_character(new_entity_name, new_entityType) : show_character_creation = false" />
					</div>
				</div>
				<EntityCard
					v-for="entity in entities.filter((e) =>
						e.entityType == 'npc'
						&& e.name.toLowerCase().indexOf(search.trim().toLowerCase()) != -1
						&& (
							(player.is_gm && (!show_archetypes && !e.isArchetype)
							|| (show_archetypes && e.isArchetype))
						)
					)"
					:key="entity.key"
					:entity_id="entity.id"
					@refresh_favorites="retrieve_entities"
					override_click
					@click_entity="switch_character(entity)" />
			</div>
		</div>
		<h1 v-if="player.is_gm" @click="display_factions" :class="[{ 'current': show_factions }, { 'next': show_npcs }]">factions</h1>
		<div id="factions" v-if="player.is_gm">
			<div class="entities" v-if="show_factions">
				<div class="entity-card no-image">
					<div class="card-wrapper clicker" v-if="!show_character_creation" @click="new_entityType = 'faction'; show_character_creation = true">
						+
					</div>
					<div class="card-wrapper" v-else>
						<input type="text" :placeholder="'add ' + new_entityType" v-model="new_entity_name" />
						<input type="button" class="button"
							:value="new_entity_name ? 'add' : 'cancel'"
							@click="new_entity_name ? create_character(new_entity_name, new_entityType) : show_character_creation = false" />
					</div>
				</div>
				<EntityCard v-for="entity in entities.filter((e) => e.entityType == 'faction' && e.name.toLowerCase().indexOf(search.trim().toLowerCase()) != -1)" :key="entity.key"
					:entity_id="entity.id" @refresh_favorites="retrieve_entities"
					override_click
					@click_entity="switch_character(entity)" />
			</div>
		</div>
		<h1 v-if="player.is_gm" @click="display_assets" :class="[{ 'current': show_assets }, { 'next': show_factions }]">assets</h1>
		<div id="assets" v-if="player.is_gm">
			<div class="entities" v-if="show_assets">
				<div class="entity-card no-image">
					<div class="card-wrapper clicker" v-if="!show_character_creation" @click="new_entityType = 'asset'; show_character_creation = true">
						+
					</div>
					<div class="card-wrapper" v-else>
						<input type="text" :placeholder="'add ' + new_entityType" v-model="new_entity_name" />
						<input type="button" class="button"
							:value="new_entity_name ? 'add' : 'cancel'"
							@click="new_entity_name ? create_character(new_entity_name, new_entityType) : show_character_creation = false" />
					</div>
				</div>
				<EntityCard v-for="entity in entities.filter((e) => e.entityType == 'asset' && e.name.toLowerCase().indexOf(search.trim().toLowerCase()) != -1)" :key="entity.key"
					:entity_id="entity.id" @refresh_favorites="retrieve_entities"
					override_click
					@click_entity="switch_character(entity)" />
			</div>
		</div>
		<div class="entities" v-if="!show_characters && !show_npcs && !show_factions && !show_assets">
			<div class="entity-card no-image">
				<div class="card-wrapper clicker" v-if="!show_character_creation" @click="show_character_creation = true">
					+
				</div>
				<div class="card-wrapper" v-else>
					<input type="text" :placeholder="'add ' + new_entityType" v-model="new_entity_name" />
					<select name="entity-type" id="entity-type" v-model="new_entityType" v-if="player.is_gm">
						<option value="character">Character</option>
						<option value="npc">NPC</option>
						<option value="asset">Asset</option>
						<option value="faction">Faction</option>
					</select>
					<input type="button" class="button"
						:value="new_entity_name ? 'add' : 'cancel'"
						@click="new_entity_name ? create_character(new_entity_name, new_entityType) : show_character_creation = false" />
				</div>
			</div>
		</div>
		<div class="scroll-space"></div>
	</div>
</template>

<style scoped>
	#character-overview-wrapper {
		padding-bottom: 80px;
		h1 {
			position: sticky;
			z-index: 1;
			text-shadow: var(--text-shadow);
			cursor: pointer;
			&.current {
				top: 0;
			}
			&.next {
				bottom: 0;
			}
			&:hover {
				color: var(--color-highlight);
			}
		}
		.wrapper {
			text-align: center;
		}
		#search {
			width: 100%;
			display: flex;
			justify-content: center;
			input {
				width: 50%;
				font-size: 1.4em;
				padding: .2em .6em;
			}
		}
		#filters {
			padding: 1em 0;
		}
		.entities {
			display: flex;
			flex-wrap: wrap;
			justify-content: center;
			gap: 1em;
		}
		.character.available {
			color: var(--color-text);
		}
		.scroll-space {
			height: 8em;
		}
	}
</style>

<style>
	.landscape {
		#character-overview-wrapper {
			padding-top: 4em;
		}
	}
</style>
