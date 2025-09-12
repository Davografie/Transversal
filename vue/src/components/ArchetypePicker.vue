<script setup lang="ts">
	import { ref, watch } from 'vue'
	import { useEntity } from '@/composables/Entity'
	import { useEntityList } from '@/composables/EntityList'

	const props = defineProps<{
		entity_id: string
		entity_type: string
	}>()

	const { entity, retrieve_entity, set_archetype } = useEntity(undefined, props.entity_id)
	const { entities, retrieve_archetypes } = useEntityList(undefined, props.entity_type)

	retrieve_entity()
	retrieve_archetypes(props.entity_type)

	const selected_archetype = ref<string | null>(entity.value.archetype?.id ?? null)

	function select_archetype() {
		console.log('selecting archetype: ' + selected_archetype.value)
		if(selected_archetype.value) {
			// update_entity({ "archetypeId": selected_archetype.value })
			set_archetype(selected_archetype.value)
		}
	}

	watch(() => entity.value.archetype, (newArchetype) => {
		if(newArchetype) {
			selected_archetype.value = newArchetype.id
		}
		else {
			selected_archetype.value = null
		}
	})
</script>

<template>
	<div class="archetype-picker">
		<select v-model="selected_archetype" @change="select_archetype">
			<option :value="null">None</option>
			<option v-for="archetype in entities" :key="archetype.id" :value="archetype.id">{{ archetype.name }}</option>
		</select>
	</div>
</template>

<style scoped>
	.archetype-picker {
		display: inline-block;
	}
</style>
