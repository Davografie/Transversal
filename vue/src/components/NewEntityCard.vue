<script setup lang="ts">
	import { ref, type Ref } from 'vue'
	import { useRouter } from 'vue-router'

	import { usePlayer } from '@/stores/Player'

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
	const player = usePlayer()

	const show_entity_creation = ref(false)
	const new_entity_name: Ref<string> = ref('')
	const new_entityType: Ref<string> = ref(props.entity_type ?? 'npc')

	const { create_entity } = useEntityList()
	const { entity, retrieve_small_entity, clone_entity } = useEntity(undefined, props.archetype_id)
	retrieve_small_entity()

	function add_entity() {
		if(!props.archetype_id) {
			create_entity(new_entity_name.value, new_entityType.value, props.location_id)
		}
		else {
			clone_entity(new_entity_name.value).then(() => {
				if(player.is_player && entity.value?.id != props.archetype_id) {
					player.player_character_key = entity.value?.key
					router.push({ path: '/entity/' + entity.value?.key })
				}
			})
		}
		emit('created_entity')
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
			.entity-type-wrapper {
				flex-grow: 1;
				display: flex;
				align-items: end;
			}
			.entity-name {
				width: 100%;
				text-align: center;
				font-size: 1.2em;
				flex-grow: 1;
			}
			.apply {
				flex-grow: 1;
				width: 100%;
			}
		}
		.options {
			.inputs {
				display: flex;
				flex-direction: column;
				width: 100%;
				height: 100%;
				justify-content: space-evenly;
				option {
					flex: 0 0 10px;
				}
			}
		}
	}
</style>
