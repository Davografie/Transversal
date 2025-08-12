<script setup lang="ts">
	import { ref, computed, watch } from 'vue'
	import LocationSelector from '@/components/LocationSelector.vue'
	import { useLocation } from '@/composables/Location'

	const props = defineProps<{
		location_key: string,
		locations_enabled?: string[],
		locations_disabled?: string[]
	}>()

	const emit = defineEmits(['update'])

	const { location, retrieve_location } = useLocation(undefined, props.location_key)
	retrieve_location()

	const locations_disabled = ref(props.locations_disabled ?? [])
	const locations_enabled = ref(props.locations_enabled ?? [])

	watch(props, () => {
		locations_disabled.value = props.locations_disabled ?? []
		locations_enabled.value = props.locations_enabled ?? []
	})

	const symbol = computed(() => {
		if(locations_enabled.value.includes(location.value.id)) {
			return '✓'
		}
		else if(locations_disabled.value.includes(location.value.id)) {
			return '✕'
		}
		else {
			return 'o'
		}
	})

	function toggle_location() {
		console.log('toggling location: ', location.value.id)
		if(locations_enabled.value.includes(location.value.id)) {
			// locations_enabled.value.splice(locations_enabled.value.indexOf(location.value.id), 1)
			locations_enabled.value = locations_enabled.value.filter(id => id !== location.value.id)
			if(locations_disabled.value.length > 0) {
				locations_disabled.value = [location.value.id, ...locations_disabled.value]
			}
			else {
				locations_disabled.value = [location.value.id]
			}
		}
		else if(locations_disabled.value.includes(location.value.id)) {
			console.log('removing disabled location: ', location.value.id, ' at index: ', locations_disabled.value.indexOf(location.value.id))
			// locations_disabled.value.splice(locations_disabled.value.indexOf(location.value.id), 1)
			locations_disabled.value = locations_disabled.value.filter(id => id !== location.value.id)
		}
		else {
			if(locations_enabled.value.length > 0) {
				locations_enabled.value = [location.value.id, ...locations_enabled.value]
			}
			else {
				locations_enabled.value = [location.value.id]
			}
		}
		emit('update', locations_enabled.value, locations_disabled.value)
	}

	const show_zones = ref<boolean>(false)
</script>

<template>
	<div class="location-selector">
		<div>
			<span @click="toggle_location">
				{{ symbol }}
				{{ location.name }}
			</span>
			<input type="button" class="button"
				v-if="location.zones && location.zones.length > 0"
				:value="show_zones ? '▲' : '▼'"
				@click="show_zones = !show_zones">
		</div>
		<div v-if="show_zones">
			<LocationSelector v-for="zone in location.zones" :key="zone.key"
				:location_key="zone.key" :locations_enabled="locations_enabled" :locations_disabled="locations_disabled" @update="(le, ld) => emit('update', le, ld)" />
		</div>
	</div>
</template>

<style scoped>
	.location-selector {
		padding-left: 1em;
		margin-left: 1em;
		text-align: left;
		border-left: 1px solid var(--color-border);
	}
</style>
