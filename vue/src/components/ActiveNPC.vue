<script setup lang="ts">
	import { ref, computed, watch, onMounted } from 'vue'

	import { useElementBounding } from '@vueuse/core'

	import { usePlayer } from '@/stores/Player'

	import { useEntity } from '@/composables/Entity'
	import { useRelation } from '@/composables/Relation'
	
	import Traitset from '@/components/Traitset.vue'
	import type { Relation } from '@/interfaces/Types'

	const props = defineProps<{
		entity_id: string
	}>()

	const emit = defineEmits([
		'hide_entity',
		'show_entity'
	])

	const player = usePlayer()

	const {
		entity,
		set_entity_id,
		retrieve_small_entity,
		retrieve_entity,
		retrieve_followers,
		create_relation,
		entity_type_icon,
		clone_entity,
		set_location
	} = useEntity(undefined, props.entity_id)

	retrieve_small_entity()

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


	// check to see if the entity of this card can be added as a relation
	const relation_possible = computed(() => {
		if(player.is_gm && player.perspective.id) {
			return !player.perspective.relations?.map(r => r.toEntity.id).includes(entity.value.id) &&
				player.perspective.id != entity.value.id
		}
		else if(!player.is_gm && player.player_character) {
			return !player.player_character.relations?.map(r => r.toEntity.id).includes(entity.value.id) &&
				player.player_character.id != entity.value.id
		}
	})

	const image = ref()
	const { width: image_width } = useElementBounding(image)
	const card_width = Math.min(entity.value.image?.width ?? 1000, 400)

	const image_link_large = computed(() => {
		return '/assets/uploads/' + entity.value.image?.path +
			'large' + entity.value.image?.ext
	})

	const image_link_small = computed(() => {
		return '/assets/uploads/' + entity.value.image?.path +
			'small' + entity.value.image?.ext
	})

	// add the entity of this card as a relation to the codex of the entity that's currently being played with
	function click_tag() {
		if(player.is_gm && player.perspective) {
			create_relation(player.perspective.id)
			setTimeout(() => player.retrieve_perspective_relations(), 100)
		}
		else if(!player.is_gm && player.player_character) {
			create_relation(player.player_character.id)
			setTimeout(() => player.retrieve_relations(), 100)
		}
		retrieve_small_entity()
		setTimeout(() => {
			set_relation_id(player.the_entity?.relations?.find(r => r.toEntity.id == props.entity_id)?.id ?? '')
		}, 200)
	}

	// when the player wants to follow the entity instead of transversing themselves
	const followable = computed(() => {
		return player.the_entity?.following?.id != entity.value.id	// already following
			&& player.the_entity?.id != entity.value.id				// can't follow yourself
			&& entity.value.following?.id != player.the_entity?.id	// can't follow that which follows you
			&& player.the_entity?.entityType != 'location'			// locations can't follow
			&& !entity.value.isArchetype							// archetypes aren't actually part of the environment (yet)
	})

	function click_follow() {
		player.is_player ? player.set_location(entity.value) : player.set_perspective_location(entity.value)
	}

	function click_unfollow() {
		if(player.the_entity?.location) {
			player.is_player ? player.set_location(player.the_entity.location) : player.set_perspective_location(player.the_entity.location)
		}
	}

	function click_import() {
		if(player.the_entity?.location) {
			set_location(player.the_entity.location)
		}
	}

	function switch_perspective(entity_id: string) {
		player.set_perspective_id(entity_id)
		player.retrieve_perspective()
	}

	function remove_relation() {
		delete_relation()
		player.is_gm ?
			setTimeout(() => player.retrieve_perspective_relations(), 100) :
			setTimeout(() => player.retrieve_relations(), 100)
	}

	onMounted(() => {
		retrieve_entity()
		retrieve_followers()
		if(player.the_entity?.relations?.map(r => r.toEntity.id).includes(props.entity_id)) {
			retrieve_relation()
		}
	})

	watch(() => props.entity_id, (newEntity, oldEntity) => {
		if(newEntity != oldEntity && newEntity != entity.value.id) {
			set_entity_id(newEntity)
			retrieve_entity()
			retrieve_followers()
			if(player.the_entity?.relations?.map(r => r.toEntity.id).includes(newEntity)) {
				set_relation_id(player.the_entity?.relations?.find(r => r.toEntity.id == newEntity)?.id || '')
				retrieve_relation()
			}
			else {
				relation.value = {} as Relation
			}
		}
	})
</script>

<template>
	<div class="active-npc">
		<div class="card">
			<img :src="player.data_saving ? image_link_small : image_link_large" ref="image" />
			<div class="close-button" @click="emit('hide_entity')">
				<span class="button-mnml icon">✖</span>
			</div>
			<div class="buttons">
				<div class="button-mnml entity-type-icon"
						@click.stop="switch_perspective(entity.id)"
						v-if="player.is_gm && player.the_entity?.id != entity.id">
					<span class="icon">{{ entity_type_icon }}</span>
					<span class="label">{{ player.small_buttons ? '' : 'take control'}}</span>
				</div>
				<div class="button-mnml entity-type-icon"
						@click.stop="emit('show_entity', entity.key)"
						v-if="player.is_gm && player.the_entity?.id != entity.id && player.orientation == 'vertical'">
					<span class="icon">👁</span>
					<span class="label">{{ player.small_buttons ? '' : 'open entity'}}</span>
				</div>
				<div class="button-mnml codex-button"
						:class="{ 'small-button': !player.small_buttons }"
						@click.stop="click_tag"
						v-if="relation_possible">
					<span class="icon">🏷</span>
					<span class="label">{{ player.small_buttons ? '' : 'add to contacts'}}</span>
				</div>
				<div class="button-mnml import-button"
						@click.stop="click_import"
						v-if="player.is_gm && entity.location?.id != player.the_entity?.location?.id">
					<span class="icon">⬇</span>
					<span class="label">{{ player.small_buttons ? '' : 'import'}}</span>
				</div>
				<div class="button-mnml follow-button"
						:class="{ 'small-button': !player.small_buttons }"
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
				<div class="button-mnml copy-button"
						@click.stop="clone_entity()"
						v-if="entity.isArchetype">
					<span class="icon">⧉</span>
					<span class="label">{{ player.small_buttons ? '' : 'spawn'}}</span>
				</div>
				<div class="button-mnml remove-relation-button"
						@click.stop="remove_relation"
						v-if="player.the_entity?.relations?.map(r => r.toEntity.id).includes(entity.id)">
					<span class="icon">💔</span>
					<span class="label">{{ player.small_buttons ? '' : 'remove'}}</span>
				</div>
			</div>
		</div>
		<h2 class="name header" v-if="player.is_gm || !relation_possible">
			{{ entity.name }}
		</h2>
		<div class="description" v-if="entity.description">
			{{ entity.description }}
		</div>
		<div class="traits">
			<Traitset
				v-if="relation_exists && relation.traitsets && relation.traitsets.length > 0"
				:traitset_id="relation.traitsets[0].id"
				:entity_id="relation.id"
				:visible="true"
				expanded
				hide_title
				extensible
				relationship />
			<template v-for="traitset in entity.traitsets" :key="traitset.id + entity.id">
			<Traitset
				:traitset_id="traitset.id"
				:entity_id="entity.id"
				:visible="true"
				expanded
				hide_title
				:limit="traitset.limit"
				v-if="(player.is_player && entity.entityType != 'character' && player.the_entity?.id != entity.id)
					|| (player.is_gm && entity.entityType == 'character' && entity.id != player.the_entity?.id && traitset.id == 'Traitsets/1')" />
			</template>
		</div>
	</div>
</template>

<style scoped>
div.active-npc {
	padding-bottom: 1em;
	min-width: 16em;
	width: v-bind(card_width + 'px');
	div.card {
		position: relative;
		line-height: 0;
		img {
			max-width: 100%;
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
				&:hover {
					flex-grow: 1.4;
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
	}
}
.light {
	div.active-npc {
		.name {
			background-color: var(--color-background);
		}
	}
}
</style>
