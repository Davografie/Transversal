<script setup lang="ts">
	import { useEntity } from '@/composables/Entity'
	import { useEntityList } from '@/composables/EntityList'

	const props = defineProps<{
		entity_id: string
		entity_type: string
	}>()

	const { entity, retrieve_entity, update_entity } = useEntity(undefined, props.entity_id)
	const { entities, retrieve_archetypes } = useEntityList(undefined, props.entity_type)

	retrieve_entity()
	retrieve_archetypes(props.entity_type)

	function select_archetype(archetype_id: string) {
		update_entity({ "archetypeId": archetype_id })
	}

	function remove_archetype() {
		update_entity({ "archetypeId": "" })
	}
</script>

<template>
	<div class="archetype-picker">
		<select :value="entity.archetype?.id">
			<option value="" @click="remove_archetype">None</option>
			<option v-for="archetype in entities" :key="archetype.id" :value="archetype.id" @click="select_archetype(archetype.id)">{{ archetype.name }}</option>
		</select>
	</div>
</template>

<style scoped>
	.archetype-picker {
		display: inline-block;
	}
</style>
