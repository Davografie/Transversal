<script setup lang="ts">
	import { ref, watch } from 'vue'
	import { useEntity } from '@/composables/Entity'
	import { useEntityList } from '@/composables/EntityList'

	import EntityCard from '@/components/EntityCard.vue'

	const props = defineProps<{
		entity_id: string
		entity_type: string
	}>()

	const { entity, retrieve_entity, set_archetype, unset_archetype } = useEntity(undefined, props.entity_id)
	const { entities, retrieve_archetypes } = useEntityList(undefined, props.entity_type)

	retrieve_entity()
	retrieve_archetypes(props.entity_type)

	const selected_archetype = ref<string | null>(entity.value.archetype?.id ?? null)
	const selected_archetypes = ref<string[]>(entity.value.archetypes?.map(archetype => archetype.id) ?? [])

	function select_archetype(archetype_id: string) {
		if(!entity.value.archetypes?.map(archetype => archetype.id).includes(archetype_id)) {
			// update_entity({ "archetypeId": selected_archetype.value })
			set_archetype(archetype_id)
		}
		else {
			// update_entity({ "archetypeId": null })
			unset_archetype(archetype_id)
		}
		setTimeout(() => {
			retrieve_entity()
		}, 200)
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
		<!-- <select v-model="selected_archetype" @change="select_archetype">
			<option :value="null">None</option>
			<option v-for="archetype in entities.filter((archetype) => archetype.id != props.entity_id)" :key="archetype.id" :value="archetype.id">{{ archetype.name }}</option>
		</select> -->
		<EntityCard
			class="entity-card"
			v-for="archetype in entities" :key="archetype.id"
			:entity_id="archetype.id"
			:entity="archetype"
			:is_active="selected_archetypes.includes(archetype.id)"
			@click="select_archetype(archetype.id)"
			override_click />
	</div>
</template>

<style scoped>
	.archetype-picker {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		.entity-card {
			width: 80px;
		}
	}
</style>
