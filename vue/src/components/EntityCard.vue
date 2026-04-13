<script setup lang="ts">
	import { ref, computed, watch, onMounted, nextTick } from 'vue'

	import { useElementBounding, useWindowSize } from '@vueuse/core'

	import { marked } from 'marked'

	import { usePlayerStore } from '@/stores/PlayerStore'

	import { useEntity } from '@/composables/Entity'
	import { useRelation } from '@/composables/Relation'
	import { useLocation } from '@/composables/Location'
	
	import Traitset from '@/components/Traitset.vue'
	import type { Relation } from '@/interfaces/Types'

	import ButtonMinimal from '@/components/UI/ButtonMinimal.vue'
	import { ButtonTypes } from '@/composables/Button'

	const props = defineProps<{
		entity_id: string
	}>()

	const emit = defineEmits([
		'hide_entity',
		'show_entity',
		'instantiated_entity',
	])

	const player = usePlayerStore()

	const {
		entity,
		set_entity_id,
		retrieve_small_entity,
		retrieve_entity,
		retrieve_archetypes,
		retrieve_followers,
		retrieve_instances,
		create_relation,
		entity_type_icon,
		clone_entity,
		set_location,
		toggle_favorite
	} = useEntity(undefined, props.entity_id)

	retrieve_entity().then(() => {
		retrieve_archetypes()
		if(entity.value.isArchetype) {
			retrieve_instances()
		}
	})

	const relation_exists = computed(() => {
		return player.the_entity?.relations?.map(r => r.toEntity.id).includes(props.entity_id)
	})

	const {
		relation,
		set_relation_id,
		retrieve_relation,
		delete_relation
	} = useRelation(
		undefined,
		relation_exists.value ?
			player.the_entity?.relations?.find(r => r.toEntity.id == props.entity_id)?.id
			: ''
	)

	const {
		location,
		retrieve_location,
		set_location_key,
		make_transversable
	} = useLocation(undefined, entity.value.key)
	
	import useClipboard from 'vue-clipboard3'
	const { toClipboard } = useClipboard()
	const copied = ref(false)
	const copy_id = async () => {
		try {
			await toClipboard(relation.value.id)
			copied.value = true
			setTimeout(() => copied.value = false, 1000)
		} catch (e) {
			console.error(e)
		}
	}


	// check to see if the entity of this card can be added as a relation
	const relation_possible = computed(() => {
		if(player.is_gm && player.perspective.id) {
			return !player.perspective.relations?.map(r => r.toEntity.id).includes(entity.value.id) &&
				player.perspective.id != entity.value.id
		}
		else if(player.is_player && player.player_character) {
			return !player.player_character.relations?.map(r => r.toEntity.id).includes(entity.value.id)
				&& player.player_character.id != entity.value.id
				&& !entity.value.isArchetype
		}
	})

	const image = ref()
	const { width: image_width } = useElementBounding(image)
	const { height: window_height } = useWindowSize()
	const card_width = computed(() => {
		if(entity.value.image?.height && entity.value.image?.width) {
			if(entity.value.image.width > entity.value.image.height) {
				return entity.value.image.width
			}
			else {
				return Math.min(entity.value.image.width, entity.value.image.width / entity.value.image.height * (window_height.value * 0.6))
			}
		}
	})

	const image_link_large = computed(() => {
		return '/assets/uploads/' + entity.value.image?.path +
			'large' + entity.value.image?.ext
	})

	const image_link_small = computed(() => {
		return '/assets/uploads/' + entity.value.image?.path +
			'small' + entity.value.image?.ext
	})

	// add the entity of this card as a relation to the codex of the entity that's currently being played with
	async function click_tag() {
		if(!player.the_entity?.id) return

		if(player.is_gm) {
			console.log("creating relation from entity " + player.the_entity.id + " to " + entity.value.id)
			const new_relation = await player.create_perspective_relation(player.the_entity?.id, entity.value.id)
			if(new_relation) {
				console.log("returned relation: ", new_relation)
				set_relation_id(new_relation.id)
				retrieve_relation()
			}
			console.log("relation created, now updating relations for " + player.the_entity.id)
			player.retrieve_perspective_relations('network-only')
		}
		else {
			await player.create_character_relation(player.the_entity?.id, entity.value.id)
			player.retrieve_character_relations('network-only')
		}
	}

	async function remove_relation() {
		if(player.is_gm && player.the_entity) {
			console.log("deleting relation from entity " + player.the_entity.id + " to " + entity.value.id)
			await player.delete_perspective_relation(relation.value.id)
			console.log("clicked 'delete relation' to entity " + entity.value.id + " now updating relations for " + player.the_entity.id)
			player.retrieve_perspective_relations('network-only')
		}
		else {
			await delete_relation()
			player.retrieve_character_relations('network-only')
		}
	}

	// when the player wants to follow the entity instead of transversing themselves
	const followable = computed(() => {
		return (		// exclusive
				player.the_entity?.following?.id != entity.value.id		// already following
				&& player.the_entity?.id != entity.value.id				// can't follow yourself
				&& entity.value.following?.id != player.the_entity?.id	// can't follow that which follows you
				// && player.the_entity?.entityType != 'location'			// locations can't follow
				&& !(
					player.is_player
					&& entity.value.location?.id != player.the_entity?.location?.id
					&& entity.value.entityType != 'location'
				)														// GM can follow from distance, players can't
				&& !entity.value.isArchetype							// archetypes aren't actually part of the environment (yet)
			)
			&& (		// inclusive
				player.is_gm
				|| (
					player.is_player
					&& entity.value.location?.id == player.the_entity?.location?.id
					&& entity.value.entityType != 'location'
				)														// player can follow characters, NPC's and assets from the same location
				|| (
					player.is_player
					&& entity.value.entityType == 'location'
				)														// fast-travel to locations
			)
	})

	async function click_follow() {
		if(player.is_player) {
			await player.set_character_location(entity.value)
			retrieve_followers('network-only')
		}
		else {
			player.set_perspective_location(entity.value)
		}
	}

	function click_unfollow() {
		if(player.the_entity?.location) {
			player.is_player ? player.set_character_location(player.the_entity.location) : player.set_perspective_location(player.the_entity.location)
		}
	}

	function click_import() {
		if(player.the_entity?.location) {
			set_location(player.the_entity.location)
		}
	}

	function switch_perspective(entity_id: string) {
		player.set_perspective(entity_id)
	}

	onMounted(() => {
		retrieve_followers()
		if(player.the_entity?.relations?.map(r => r.toEntity.id).includes(props.entity_id)) {
			retrieve_relation()
		}
	})

	async function instantiate() {
		await clone_entity(undefined, player.the_entity?.location?.id).then(new_clone => {
			console.log('instantiated entity (D): ', new_clone)
			emit('instantiated_entity', new_clone)
		})
	}

	watch(() => props.entity_id, (newEntity, oldEntity) => {
		if(newEntity != oldEntity && newEntity != entity.value.id) {
			set_entity_id(newEntity)
			retrieve_entity().then(() => {
				retrieve_archetypes()
				if(entity.value.isArchetype) {
					retrieve_instances()
				}
			})
			if(player.the_entity?.relations?.map(r => r.toEntity.id).includes(newEntity)) {
				set_relation_id(player.the_entity?.relations?.find(r => r.toEntity.id == newEntity)?.id || '')
				retrieve_relation()
			}
			else {
				relation.value = {} as Relation
			}
		}
	})
	watch(() => entity.value.id, () => {
		retrieve_archetypes()
		retrieve_followers()
	})
	watch(entity, (newEntity) => {
		if(entity.value.entityType == 'location') {
			set_location_key(newEntity.key)
			retrieve_location()
		}
		const element = document.getElementById('active-npc')
		if(element) {
			element.scrollIntoView({ behavior: 'smooth', block: 'center' })
		}
	})

	const show_archetypes = ref(false)
	const show_sub_archetypes = ref(false)
	const show_instances = ref(false)
</script>

<template>
	<div class="active-npc">
		<div class="card">
			<div id="active-npc" class="image" @click.stop="player.image_entity = entity">
				<img :src="player.data_saving ? image_link_small : image_link_large" ref="image" />
			</div>
			<div class="close-button" @click="emit('hide_entity')">
				<span class="button-mnml icon">✖</span>
			</div>
			<div class="buttons">
				<div class="button-mnml copy-relation-id-button"
						@click.stop="copy_id"
						v-if="player.is_gm && relation?.id">
					<span class="icon">#</span>
					<span class="label" v-if="!copied">{{ player.small_buttons ? '' : 'copy relation id'}}</span>
					<span class="label" v-else>{{ player.small_buttons ? '' : 'copied!'}}</span>
				</div>
				<div class="button-mnml entity-type-icon"
						@click.stop="switch_perspective(entity.id)"
						v-if="player.is_gm && player.the_entity?.id != entity.id">
					<span class="icon">{{ entity_type_icon }}</span>
					<span class="label">{{ player.small_buttons ? '' : 'take control'}}</span>
				</div>
				<!-- <div class="button-mnml entity-type-icon"
						@click.stop="emit('show_entity', entity.key)"
						v-if="player.is_gm && player.the_entity?.id != entity.id && player.orientation == 'vertical'">
					<span class="icon">👁</span>
					<span class="label">{{ player.small_buttons ? '' : 'open entity'}}</span>
				</div> -->
				<ButtonMinimal :function="ButtonTypes.RELATION"
					@click.stop="click_tag"
					v-if="relation_possible" />
				<div class="button-mnml remove-relation-button"
						@click.stop="remove_relation"
						v-if="player.the_entity?.relations?.filter(r => r.toEntity.id != player.the_entity?.id).map(r => r.toEntity.id).includes(entity.id)">
					<span class="icon">💔</span>
					<span class="label">{{ player.small_buttons ? '' : 'remove'}}</span>
				</div>
				<div class="button-mnml transversable-button"
						:class="{ 'small-button': !player.small_buttons }"
						@click.stop="make_transversable(player.the_entity?.id)"
						v-if="player.the_entity?.entityType == 'location' && entity.entityType == 'location'">
					<span class="icon">⤠</span>
					<span class="label">{{ player.small_buttons ? '' : 'make transversable'}}</span>
				</div>
				<div class="button-mnml import-button"
						@click.stop="click_import"
						v-if="player.is_gm && entity.location?.id != player.the_entity?.location?.id">
					<span class="icon">⬇</span>
					<span class="label">{{ player.small_buttons ? '' : 'import'}}</span>
				</div>
				<div class="button-mnml follow-button"
						:class="[{ 'small-button': !player.small_buttons }, { 'disabled': player.the_entity?.location?.id == entity.id }]"
						@click.stop="click_follow"
						v-if="followable">
					<span class="icon">⬆</span>
					<span class="label">{{ player.small_buttons ? '' : entity.entityType != 'location' ? 'follow' : 'transverse'}}</span>
				</div>
				<div class="button-mnml unfollow-button"
						@click.stop="click_unfollow"
						v-if="player.the_entity?.following && player.the_entity?.following.id == entity.id">
					<span class="icon">⍏</span>
					<span class="label">{{ player.small_buttons ? '' : 'unfollow'}}</span>
				</div>
				<ButtonMinimal :function="ButtonTypes.ADD_ARCHETYPE"
					v-if="![player.the_entity, ...player.the_entity?.archetypes].map(arch => arch.id).includes(entity.id) && entity.isArchetype"
					label="assume archetype"
					@click.stop="player.set_perspective_archetype(entity.id)" />
				<ButtonMinimal :function="ButtonTypes.REMOVE_ARCHETYPE"
					v-if="player.the_entity?.archetypes?.map(arch => arch.id).includes(entity.id) && entity.isArchetype"
					@click.stop="player.unset_perspective_archetype(entity.id)" />
				<div class="button-mnml copy-button"
						@click.stop="instantiate"
						v-if="entity.isArchetype && player.is_gm">
					<span class="icon">⧉</span>
					<span class="label">{{ player.small_buttons ? '' : 'spawn'}}</span>
				</div>
				<div class="button-mnml favorite-button"
						@click.stop="toggle_favorite"
						v-if="player.is_gm">
					<span class="icon" v-if="entity.favorite">★</span>
					<span class="icon" v-else>☆</span>
					<span class="label" v-if="!entity.favorite">{{ player.small_buttons ? '' : 'favorite'}}</span>
					<span class="label" v-else>{{ player.small_buttons ? '' : 'unfavorite'}}</span>
				</div>
			</div>
		</div>
		<span class="location" v-if="entity.location?.name" @click="emit('show_entity', entity.location.key)">
			🗺 {{ entity.location.name }}
		</span>
		<h2 class="name header" v-if="player.is_gm || !relation_possible">
			{{ entity.name }}
		</h2>
		<div class="description" v-if="entity.description && player.is_gm" v-html="marked.parse(entity.description)">
		</div>
		<!-- <h4 v-if="(entity.archetypes?.length || 0) > 0 && player.is_gm">archetypes</h4> -->
		<div class="entity-links">
			<div class="entity-links archetypes" v-if="player.is_gm">
				<span class="entity-link archetype"
					@click="show_archetypes = !show_archetypes"
					v-if="(entity.archetypes?.filter(a => a.name).length ?? 0) > 0"
					:class="{ 'active': show_archetypes }">{{ entity.archetypes?.filter(a => a.name).length ?? 0 }} archetypes</span>
				<span class="entity-link archetype"
						v-if="show_archetypes"
						v-for="archetype in entity.archetypes?.filter(a => a.name)" :key="archetype.id"
					@click="emit('show_entity', archetype.key)">
					{{ archetype.name }}
				</span>
			<!-- </div> -->
			<!-- <h4 v-if="(entity.instances?.filter(i => i.isArchetype).length || 0) > 0 && player.is_gm">sub-archetypes</h4> -->
			<!-- <div class="entity-links sub-archetypes" v-if="player.is_gm"> -->
				<span class="entity-link sub-archetype"
					@click="show_sub_archetypes = !show_sub_archetypes"
					v-if="(entity.instances?.filter(i => i.isArchetype).length ?? 0) > 0"
					:class="{ 'active': show_sub_archetypes }">{{ entity.instances?.filter(i => i.isArchetype).length ?? 0 }} sub-archetypes</span>
				<span class="entity-link sub-archetype"
						v-if="show_sub_archetypes"
						v-for="instance in entity.instances?.filter(i => i.isArchetype)" :key="instance.id"
					@click="emit('show_entity', instance.key)">
					{{ instance.name }}
				</span>
			<!-- </div> -->
			<!-- <h4 v-if="(entity.instances?.filter(i => !i.isArchetype).length || 0) > 0 && player.is_gm">instances</h4> -->
			<!-- <div class="entity-links instances" v-if="player.is_gm"> -->
				<span class="entity-link instance"
					@click="show_instances = !show_instances"
					v-if="(entity.instances?.filter(i => !i.isArchetype).length ?? 0) > 0"
					:class="{ 'active': show_instances }">{{ entity.instances?.filter(i => !i.isArchetype).length ?? 0 }} instances</span>
				<span class="entity-link instance"
						v-if="show_instances"
						v-for="instance in entity.instances?.filter(i => !i.isArchetype)" :key="instance.id"
					@click="emit('show_entity', instance.key)">
					{{ instance.name }}
				</span>
			</div>
		</div>
		<div class="traits">
			<Suspense>
				<Traitset
					v-if="relation_exists && relation.traitsets && relation.traitsets.length > 0"
					:traitset_id="relation.traitsets[0].id"
					:entity_id="relation.id"
					:visible="true"
					expanded
					hide_title
					extensible
					relationship />
			</Suspense>
			<template v-for="traitset in entity.traitsets" :key="traitset.id + entity.id">
				<Suspense>
					<Traitset
						:traitset_id="traitset.id"
						:entity_id="entity.id"
						expanded
						hide_title
						:limit="traitset.limit"
						v-if="(player.is_player && entity.entityType != 'character' && player.the_entity?.id != entity.id && !traitset.entityTypes?.includes('relation'))
							|| (player.is_gm && entity.entityType == 'character' && entity.id != player.the_entity?.id && traitset.id == 'Traitsets/1')" />
				</Suspense>
			</template>
		</div>
	</div>
</template>

<style scoped>
div.active-npc {
	padding-bottom: 1em;
	/* min-width: 16em; */
	width: v-bind(card_width + 'px');
	max-width: 100%;
	div.card {
		position: relative;
		line-height: 0;
		.image {
			/* min-height: 200px; */
			img {
				max-width: 100%;
			}
		}
		.close-button {
			position: absolute;
			top: .4em;
			right: 0;
			padding: .3em;
			font-size: 2em;
			text-shadow: var(--text-shadow);
		}
		.buttons {
			line-height: normal;
			/* position: absolute; */
			bottom: 0;
			display: flex;
			width: 100%;
			overflow-x: auto;
			background-color: var(--color-background);
			.button-mnml {
				flex-grow: 1;
				padding: .3em;
				font-size: 1.2em;
				display: flex;
				flex-direction: column;
				&.favorite-button {
					color: var(--color-gm);
				}
				&:hover {
					flex-grow: 1.4;
				}
			}
		}
	}
	.entity-links {
		display: flex;
		/* justify-content: space-evenly; */
		gap: .4em;
		flex-wrap: wrap;
		padding: .4em;
		width: 100%;
		.entity-link {
			border: 1px solid var(--color-gm);
			padding: .2em .4em;
			flex-grow: 1;
			transition: background-color 1s ease-out, flex-grow .2s ease-in-out;
			&.active {
				text-decoration: line-through;
			}
			&:hover {
				flex-grow: 2;
				&.archetype {
					background-color: var(--color-background);
				}
				&.sub-archetype {
					background-color: var(--color-background-mute);
				}
				&.instance {
					background-color: var(--color-gm);
				}
			}
		}
	}
	.description {
		font-style: italic;
	}
}
</style>

<style>
.dark {
	div.active-npc {
		border-radius: 30px;
		/* overflow: hidden; */
		box-shadow: 0 0 20px var(--color-background);
		background-color: var(--color-background-mute);
		img {
			border-radius: 30px 30px 0 0;
		}
		.entity-links {
			.entity-link {
				&.archetype {
					background-color: var(--color-background-mute);
				}
				&.sub-archetype {
					background-color: var(--color-gm-mute);
				}
				&.instance {
					background-color: var(--color-gm-light);
				}
			}
		}
	}
}
.light {
	div.active-npc {
		background-color: var(--color-background);
		border: 4px double var(--color-border);
		.archetype {
			color: var(--color-gm);
		}
	}
}
</style>
