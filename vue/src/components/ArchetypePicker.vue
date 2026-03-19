<script setup lang="ts">
	import { ref, watch } from 'vue'
	import { useEntity } from '@/composables/Entity'
	import { useEntityList } from '@/composables/EntityList'

	import EntityButton from '@/components/EntityButton.vue'

	const props = defineProps<{
		entity_id: string
		entity_type: string
		location_id?: string
	}>()

	const emit = defineEmits(['update_archetype'])

	const {
		entity,
		retrieve_small_entity,
		retrieve_archetypes: retrieve_entity_archetypes,
		set_archetype,
		unset_archetype
	} = useEntity(undefined, props.entity_id)

	const {
		entities,
		retrieve_archetypes
	} = useEntityList(undefined, props.entity_type)

	retrieve_small_entity()
	retrieve_entity_archetypes()
	retrieve_archetypes(props.entity_type, props.location_id)

	const selected_archetype = ref<string | null>(entity.value.archetype?.id ?? null)
	const selected_archetypes = ref<string[]>(entity.value.archetypes?.map(archetype => archetype.id) ?? [])

	async function select_archetype(archetype_id: string) {
		if(!entity.value.archetypes?.map(archetype => archetype.id).includes(archetype_id)) {
			// update_entity({ "archetypeId": selected_archetype.value })
			await set_archetype(archetype_id)
		}
		else {
			// update_entity({ "archetypeId": null })
			await unset_archetype(archetype_id)
		}
		emit('update_archetype')
		// setTimeout(() => {
		// 	retrieve_entity_archetypes()
		// }, 200)
	}

	watch(() => entity.value.archetype, (newArchetype) => {
		if(newArchetype) {
			selected_archetype.value = newArchetype.id
		}
		else {
			selected_archetype.value = null
		}
	})
	watch(() => entity.value.archetypes, (newArchetypes) => {
		if(newArchetypes) {
			selected_archetypes.value = newArchetypes.map(archetype => archetype.id)
		}
		else {
			selected_archetypes.value = []
		}
	})
</script>

<template>
	<div class="archetype-picker">
		<div class="banner">
			<h3>pick archetypes</h3>
			<span>each archetype has several traits which will be inherited when selected</span>
		</div>
		<div class="archetypes">
			<EntityButton
				class="entity-card"
				v-for="archetype in entity.archetypes" :key="archetype.id"
				:entity_id="archetype.id"
				:is_active="true"
				@click="select_archetype(archetype.id)"
				override_click
				show_archetypes />
			<EntityButton
				class="entity-card"
				v-for="archetype in entities.filter((archetype) => archetype.id != props.entity_id && !entity.archetypes?.map(archetype => archetype.id).includes(archetype.id))" :key="archetype.id"
				:entity_id="archetype.id"
				:is_active="selected_archetypes.includes(archetype.id)"
				@click="select_archetype(archetype.id)"
				override_click
				show_archetypes />
		</div>
	</div>
</template>

<style scoped>
	.archetype-picker {
		.banner {
			padding: 0 1em;
		}
		.archetypes {
			padding: 1em;
			display: flex;
			flex-wrap: wrap;
			justify-content: space-evenly;
			gap: 1rem;
			max-height: 30vh;
			overflow-y: auto;
			.entity-card {
				width: 80px;
			}
		}
	}
</style>
