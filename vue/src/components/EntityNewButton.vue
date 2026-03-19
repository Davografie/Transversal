<script setup lang="ts">
	import { ref, type Ref } from 'vue'
	import { useRouter } from 'vue-router'

	import { usePlayerStore } from '@/stores/PlayerStore'

	import { useEntityList } from '@/composables/EntityList'
	import { useEntity } from '@/composables/Entity'

	const props = defineProps<{
		location_id: string,
		entity_type?: string,
		archetype_id?: string,
		options_direction?: string
	}>()

	const emit = defineEmits(['created_entity'])

	const router = useRouter()
	const player = usePlayerStore()

	const show_entity_creation = ref(false)
	const new_entity_name: Ref<string> = ref('')
	const new_entityType: Ref<string> = ref(props.entity_type ?? 'npc')
	const new_is_archetype: Ref<boolean> = ref(false)

	const { create_entity } = useEntityList()
	const { entity, retrieve_small_entity, clone_entity } = useEntity(undefined, props.archetype_id)
	retrieve_small_entity()

	async function add_entity() {
		if(!props.archetype_id) {
			const new_entity = await create_entity(new_entity_name.value, new_entityType.value, props.location_id)
			player.is_gm ? player.set_perspective(new_entity.id) : player.set_character_id(new_entity.id)
			emit('created_entity', new_entity)
		}
		else {
			// clone_entity(new_entity_name.value).then(() => {
			// 	if(player.is_player && entity.value?.id != props.archetype_id) {
			// 		player.player_character_key = entity.value?.key
			// 		router.push({ path: '/entity/' + entity.value?.key })
			// 	}
			// })
			const new_entity = await clone_entity(new_entity_name.value)
			console.log('cloned entity: ', new_entity)
			if(player.is_player && new_entity.id != props.archetype_id) {
				player.player_character_key = new_entity.key
				player.retrieve_character()
				router.push({ path: '/entity/' + new_entity.key })
			}
			else {
				emit('created_entity', new_entity)
			}
		}
		new_entity_name.value = ''
		show_entity_creation.value = false
	}
</script>

<template>
	<div class="entity-card no-image new-entity" :class="{'editing': show_entity_creation}">
		<div class="card-wrapper clicker" :class="show_entity_creation ? 'creating' : 'default'"
			@click="show_entity_creation = !show_entity_creation">
			{{ show_entity_creation ? 'x' : '+'}}
		</div>
		<div class="options" :class="props.options_direction" v-if="show_entity_creation">
			<div class="inputs">
				<div class="entity-type-wrapper">
					<select name="entity-type"
							id="entity-type"
							class="option"
							v-model="new_entityType"
							v-if="player.is_gm"
							@click.stop>
						<option value="character">Character</option>
						<option value="npc">NPC</option>
						<option value="asset">Asset</option>
						<option value="faction">Faction</option>
					</select>
					<div class="archetype-option">
						<input type="checkbox" id="is-archetype" v-model="new_is_archetype" v-if="player.is_gm" />
						<label for="is-archetype" class="option" v-if="player.is_gm && !player.small_buttons">archetype</label>
					</div>
				</div>
				<input class="entity-name option"
					type="text" :placeholder="'add ' + new_entityType"
					v-model="new_entity_name"
					@click.stop />
					<input type="button"
						class="button-mnml apply option"
						:value="new_entity_name ? 'add' : 'cancel'"
						@click.stop="new_entity_name ? add_entity() : show_entity_creation = false" />
			</div>
		</div>
	</div>
</template>

<style scoped>
	.entity-card.new-entity {
		.card-wrapper {
			justify-content: center;
			align-items: center;
			&.creating {
				z-index: 1;
				background-color: var(--color-background);
			}
		}
	}
	.entity-card.new-entity.editing {
		width: 200px;
		.card-wrapper {
			padding: 0;
			justify-content: space-evenly;
			overflow: hidden;
		}
		.options {
			.inputs {
				width: 100%;
				height: 100%;
				display: flex;
				flex-direction: column;
				justify-content: space-evenly;
				gap: .4em;
				padding: .4em;
				option {
					flex: 0 0 10px;
				}
				.entity-type-wrapper {
					flex-grow: 1;
					display: flex;
					align-items: center;
					justify-content: space-around;
					gap: 1em;
				}
				.entity-name {
					width: 100%;
					min-width: 6em;
					text-align: center;
					font-size: 1.2em;
					flex-grow: 1;
				}
				.apply {
					flex-grow: 1;
					width: 100%;
				}
			}
		}
	}
</style>
