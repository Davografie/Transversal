<script setup lang="ts">
	import { useLocation } from '@/composables/Location'
	import { RouterLink } from 'vue-router'
	const props = defineProps<{
		location_id: string
	}>()
	const { location, retrieve_location } = useLocation(undefined, props.location_id)
	retrieve_location()
</script>

<template>
	<div class="resolution-location-wrapper">
		<RouterLink :to="'/location/' + location.key">
			{{ location.name }}
		</RouterLink>
	</div>
</template>

<style scoped>
</style>
