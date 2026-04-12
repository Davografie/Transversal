<script setup lang="ts">
import { useLocation } from '@/composables/Location'
const props = defineProps<{
	location_id: string
}>()
const { location, retrieve_location, retrieve_parents } = useLocation(undefined, props.location_id)
retrieve_location().then(() => {
	retrieve_parents()
})
</script>

<template>
	<div class="location-picker">
		<div v-for="parent in location.parents" :key="parent.key">
			{{  parent.name }}
		</div>
	</div>
</template>

<style scoped>
</style>
