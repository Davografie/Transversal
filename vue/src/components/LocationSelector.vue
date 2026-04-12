<script setup lang="ts">
	import { ref, computed, watch } from 'vue'
	import LocationSelector from '@/components/LocationSelector.vue'
	import { useLocation } from '@/composables/Location'

	const props = defineProps<{
		location_key: string,
		locations_enabled?: string[],
		locations_disabled?: string[],
		status?: string
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

	const status = computed(() => {
		if(locations_enabled.value.includes(location.value.id)) {
			return 'enabled'
		}
		else if(locations_disabled.value.includes(location.value.id)) {
			return 'disabled'
		}
		else if(props.status) {
			return props.status
		}
		else {
			return 'none'
		}
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
		console.log('locations enabled: ', locations_enabled.value, ' locations disabled: ', locations_disabled.value)
		emit('update', locations_enabled.value, locations_disabled.value)
	}

	const show_zones = ref<boolean>(false)

	const image_link = computed(() => {
		if(location.value.image) {
			// return '/assets/uploads/' + location.value.image.path + '/small' + location.value.image.ext
			return { backgroundImage: `url('/assets/uploads/${location.value.image.path}/small${location.value.image.ext}')` }
		}
	})
</script>

<template>
	<div class="location-selector" :class="status">
		<div class="location">
			<div class="location-description" @click="toggle_location" :style="show_zones ? image_link : ''">
				<div class="location-name" :class="status">
					{{ symbol }}
					{{ location.name }}
				</div>
				<!-- <img v-if="image_link && show_zones" :src="image_link" :alt="location.name" /> -->
			</div>
			<!-- <input type="button" class="button-mnml"
				v-if="location.zones && location.zones.length > 0"
				:value="show_zones ? 'x' : '+'"
				@click="show_zones = !show_zones"> -->
			<div class="button-mnml show-zones-button" v-if="location.zones && location.zones.length > 0"
				@click="show_zones = !show_zones">
				<span class="icon">{{ show_zones ? 'x' : '+' }}</span>
			</div>
		</div>
		<div v-if="show_zones" class="zones">
			<LocationSelector v-for="zone in location.zones" :key="zone.key"
				:location_key="zone.key"
				:locations_enabled="locations_enabled"
				:locations_disabled="locations_disabled"
				:status="status"
				@update="(le, ld) => emit('update', le, ld)" />
		</div>
	</div>
</template>

<style scoped>
	.location-selector {
		/* padding-left: 1em;
		margin-left: 1em;
		text-align: left;
		border-left: 1px solid var(--color-border); */
		display: flex;
		/* flex-direction: column; */
		gap: .4em;
		flex-grow: 1;
		border: 1px solid var(--color-border);
		.location {
			display: flex;
			justify-content: space-between;
			align-items: center;
			gap: .4em;
			flex-grow: 1;
			padding: .4em;
			/* background-size: cover; */
			background-repeat: no-repeat;
			backdrop-filter: blur(5px);
			/* background-color: var(--color-background-mute); */
			.location-description {
				height: 100%;
				display: flex;
				/* justify-content: center; */
				align-items: center;
				gap: .4em;
				flex-grow: 1;
				background-repeat: no-repeat;
				background-position: left center;
				background-size: contain;
				/* min-height: 3em; */
				.location-name {
					width: 100%;
					text-align: left;
				}
			}
		}
		.zones {
			display: flex;
			flex-direction: column;
			justify-content: center;
			gap: .4em;
			flex-grow: 3;
			padding: .4em;
		}
		.show-zones-button {
			background-color: var(--color-background-mute);
			height: 100%;
		}
		&.enabled, .enabled.location-name {
			background-color: var(--color-highlight);
			color: var(--color-highlight-text);
		}
		&.disabled, .disabled.location-name {
			background-color: var(--color-hitch);
			color: var(--color-hitch-text);
		}
		&.none, .none.location-name {
			background-color: var(--color-background-mute);
			color: var(--color-background-text);
		}
	}
</style>
