<script setup lang="ts">
	import { useEntity } from '@/composables/Entity'
	import { RouterLink } from 'vue-router'
	const props = defineProps<{
		entity_id: string
	}>()
	const { entity, retrieve_entity } = useEntity(undefined, props.entity_id)
	retrieve_entity()
</script>

<template>
	<div class="resolution-entity-wrapper">
		<RouterLink :to="'/entity/' + entity.key">
			{{ entity.name }}
		</RouterLink>
	</div>
</template>

<style scoped>
</style>
