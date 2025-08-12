<script setup lang="ts">
	import { ref, computed, watch } from 'vue'
	import { useRouter } from 'vue-router'

	import { usePlayer } from '@/stores/Player'

	import { useRelation } from '@/composables/Relation'
	import { useCharacter } from '@/composables/Character'
	import { useLocation } from '@/composables/Location'
	import { useEntity } from '@/composables/Entity'
	import Traitset from '@/components/Traitset.vue'

	const props = defineProps<{
		relation_id?: string,
		from_type?: string,
		to_entity_id: string,
		to_type?: string
	}>()

	const emit = defineEmits([
		'hide_codex',
		'hide_relation',
		'show_entity'
	])

	const router = useRouter()
	const player = usePlayer()

	const { relation, set_relation_id, retrieve_relation, update_relation, delete_relation } = useRelation(undefined, props.relation_id)

	const { entity, set_entity_id, retrieve_small_entity } = useEntity(undefined, undefined)

	if(props.relation_id) {
		retrieve_relation()
	}

	function populate_relation() {
		set_entity_id(props.to_entity_id)
		retrieve_small_entity()
	}

	populate_relation()

	const entity_type_icon = computed(() => {
		if(entity.value && props.to_type == 'character'){
			return "👤"
		}
		else if(entity.value && props.to_type == 'npc'){
			return "🎭"
		}
		else if(entity.value && props.to_type == 'location'){
			return "🧭"
		}
		else if(entity.value && props.to_type == 'asset'){
			return "🛠"
		}
		else if(entity.value && props.to_type == 'faction'){
			return "🛡"
		}
	})

	const image_url = computed(() => {
		if(entity.value.image) {
			return 'url("' + '/assets/uploads/' + entity.value.image.path + '/small' + entity.value.image.ext + '")'
		}
	})

	const held = ref(false)

	const editing_relation = ref(false)

	function longpress_relation() {
		held.value = true
		editing_relation.value ?
			editing_relation.value = false :
			editing_relation.value = true
		setTimeout(() => held.value = false, 500)
	}

	function favorite_relation() {
		held.value = true
		console.log('favoring relation: ', relation.value.favorite)
		editing_relation.value = false
		update_relation(!relation.value.favorite)
		setTimeout(() => held.value = false, 500)
		update_codex()
	}

	function update_codex() {
		player.is_gm ?
			player.retrieve_perspective_relations() :
			player.retrieve_relations()
	}

	function remove_relation() {
		delete_relation()
		emit('hide_relation')
		update_codex()
	}

	function click_icon() {
		// router.push({ path: '/entity/' + entity.value?.key })
		emit('hide_codex')
		emit('hide_relation')
		emit('show_entity', entity.value?.key)
	}

	function change_location() {
		if(player.is_gm) {
			player.set_perspective_location(entity.value)
		}
		else {
			player.set_location(entity.value)
		}
		emit('hide_codex')
	}

	const show_traitsets = ref(true)

	watch(props, () => {
		if(props.relation_id) {
			if(props.relation_id) set_relation_id(props.relation_id)
		}
		populate_relation()
	})
</script>

<template>
	<div class="relation" v-if="entity"
			:class="[
				{ 'favorite': relation.favorite },
				show_traitsets ? 'expanded' : 'collapsed'
			]">
		<div class="bookmark">
			<div class="character"
					@click="change_route"
					v-touch:hold="longpress_relation"
					@click.right="longpress_relation"
					@contextmenu="(e) => e.preventDefault()">
				<span class="entity-name">{{ entity.name }}</span>
			</div>
			<div class="traitsets" v-if="relation.traitsets && show_traitsets && entity.id == relation.toEntity.id">
				<Traitset v-for="set in relation.traitsets" :key="relation.id + set.id"
					:traitset_id="set.id"
					:entity_id="player.the_entity?.id ?? ''"
					:relation_id="relation.id"
					:expanded="player.editing ? set.traits && set.traits.length > 0 : true"
					:extensible="editing_relation || (set.traits && set.traits.length == 0)"
					relationship
					visible
					hide_title />
			</div>
		</div>
		<div class="buttons">
			<input type="button" class="button-mnml entity-type-icon"
				@click="click_icon" :value="entity_type_icon + (player.small_buttons ? '' : '\n' + entity.name)" />

			<input type="button" class="button-mnml transverse"
				:value="player.small_buttons ? '⬇' : '⬇\ngo to location'"
				v-if="entity.entityType == 'location'"
				@click.stop="change_location" />

			<input type="button" class="button-mnml follow"
				:value="player.small_buttons ? '⬆' : '⬆\nfollow'"
				v-if="player.is_gm && entity.entityType == 'character' && player.the_entity?.id == 'Entities/1' && player.the_entity?.following?.id != entity.id"
				@click.stop="change_location" />

			<input type="button" class="button-mnml favorite"
				:value="player.small_buttons ? '⭐' : '⭐\n' + (relation.favorite ? 'unfavorite' : 'favorite')"
				@click.stop="favorite_relation" />

			<input type="button" class="button-mnml edit-traitset"
				:value="player.small_buttons ? '✎' : '✎\n' + (editing_relation ? 'cancel' : 'edit')"
				@click.stop="editing_relation = !editing_relation" />

			<input type="button" class="button-mnml remove-relation"
				:value="player.small_buttons ? '🗑' : '🗑\nremove'"
				@click.stop="remove_relation" />
		</div>
	</div>
</template>

<style scoped>
	.relation {
		/* border-left: 1px solid var(--color-border); */
		/* flex-grow: 1; */
		&.collapsed {
			max-width: 100px;
			flex-grow: 1;
		}
		&.expanded {
			width: 100%;
		}
		.bookmark {
			min-height: 100px;
			width: 100%;
			display: flex;
			justify-content: space-between;
			background-image: v-bind(image_url);
			background-size: 100px;
			/* background-position: center 10%; */
			background-repeat: no-repeat;
			.traitsets {
				min-width: 50%;
			}
			.character {
				flex-grow: 1;
				display: flex;
				flex-direction: column;
				justify-content: end;
				cursor: pointer;
				.buttons {
					display: flex;
					justify-content: space-between;
				}
				img {
					max-height: 48px;
					max-width: 48px;
				}
				.entity-name {
					padding-left: .4em;
				}
			}
		}
		.buttons {
			width: 100%;
			display: flex;
			justify-content: space-around;
			align-items: center;
			.button-mnml {
				flex-grow: 1;
				width: 48px;
				height: 48px;
			}
		}
	}
</style>

<style>
	.light {
		.relation.favorite {
			color: var(--color-highlight);
		}
		.relation {
			.bookmark {
				.character {
					.entity-name {
						font-size: 1.2em;
						background-color: var(--color-background);
					}
				}
				.traitset {
					height: 100%;
					background-color: var(--color-background);
				}
			}
		}
	}
	.dark {
		.relation.favorite {
			color: var(--color-highlight);
		}
		.relation {
			.bookmark {
				.character {
					font-size: 1.2em;
					.entity-name {
						/* background-color: var(--color-background-mute); */
						text-shadow: var(--text-shadow);
						/* text-align: center; */
					}
					.entity-type-icon {
						opacity: .5;
					}
				}
				.traitset {
					height: 100%;
					.traits {
						height: 100%;
						.trait {
							flex-grow: 1;
						}
					}
				}
			}
			.buttons {
				background-color: var(--color-background-mute);
			}
		}
	}
</style>
