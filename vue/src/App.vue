<script setup lang="ts">
	import Mobile from '@/views/Mobile.vue'
	import Landscape from '@/views/Landscape.vue'
	import { ref, computed, watch, onMounted, onUpdated } from 'vue'
	import { useRouter, useRoute, RouterLink } from 'vue-router'
	import { useWindowSize, useElementSize, usePreferredColorScheme, useScreenOrientation, templateRef } from '@vueuse/core'

	import { usePlayer } from '@/stores/Player'
	import { useDicepoolStore } from '@/stores/DicepoolStore'
	import { useSession } from '@/composables/Session'

	import { useLocation } from '@/composables/Location'
	
	import { type Location } from '@/interfaces/Types'

	const player = usePlayer()
	player.create_player()

	const dicepool_store = useDicepoolStore()

	const { get_session, set_dicepool_limit } = useSession()
	get_session()

	const router = useRouter()
	const route = useRoute()

	const dicepool = ref(null)

	const { orientation } = useScreenOrientation()
	const { width: windowWidth, height: windowHeight } = useWindowSize()
	const preferredColor = usePreferredColorScheme()
	watch(preferredColor, () => {
		player.theme = preferredColor.value
	}, { immediate: true })
	const { height: dicepoolHeight } = useElementSize(dicepool)

	const landscape_header_height = ref<number>(24)
	const header_height = computed(() => {
		if(triptych.value) return 0
		else if(route.params.entity_key != player.the_entity?.key && !triptych) return landscape_header_height.value + 20
		else return landscape_header_height.value
	})
	const triptych = computed(() => orientation.value == "portrait-primary" || windowWidth.value <= 832)
	const third_width = computed(() => windowWidth.value / 3)

	watch(
		[windowWidth, windowHeight],
		([newWidth, newHeight]) => {
			player.orientation = newWidth > newHeight ? "horizontal" : "vertical"
		},
		{ immediate: true }
	)

	const view = ref('location')
	
	function transverse(loc: Location) {
		if(player.is_gm && player.perspective && player.perspective.entityType != 'faction') {
			player.set_perspective_location(loc)
		}
		else if(!player.is_gm && player.player_character) {
			player.set_location(loc)
		}
	}


	const overwrite_entity_key = ref<string|undefined>()

	const location_image_link = ref(
		player.the_entity?.location?.image ?
			'/assets/uploads/' + player.the_entity.location.image.path + '/original' + player.the_entity.location.image?.ext :
			''
	)

	// for in watcher when location is specified in url
	const { location, set_location_key, retrieve_small_location } = useLocation(undefined, undefined)

	watch(route, (newRoute) => {
		if(newRoute.params.location_key) {
			set_location_key(newRoute.params.location_key as string)
			retrieve_small_location()
		}
		if(
			newRoute.name == 'Location'
			&& newRoute.params.location_key
			&& player.the_entity?.location?.key
			&& player.the_entity?.location?.key != 'placeholder'
			&& newRoute.params.location_key != player.the_entity?.location?.key
		) {
			console.log('route id changed from ' + player.the_entity?.location?.key + ', retrieving location: ' + newRoute.params.location_key)
			// location_image_link.value = '/assets/uploads/' + location.value.image?.path + '/original' + location.value.image?.ext
			watch(location, () => {
				if(player.is_player) {
					player.set_location(location.value)
				}
				else {
					player.set_perspective_location(location.value)
				}
			}, { once: true })
		}
		if(newRoute.matched.length > 1 && newRoute.matched[1].name?.toString().toLowerCase() != view.value) {
			view.value = newRoute.matched[1].name?.toString().toLowerCase() ?? 'location'
			if(newRoute.params.entity_id) {
				overwrite_entity_key.value = newRoute.params.entity_id as string
			}
		}
	})

	watch(location, (newLocation) => {
		if(newLocation.image) {
			location_image_link.value = '/assets/uploads/' + newLocation.image.path + '/original' + newLocation.image?.ext
		}
		else {
			location_image_link.value = ''
		}
	})

	const app_wrapper_component = templateRef<HTMLElement>('app_wrapper_component')
	const scrolling_to_top = ref(false)

	function scroll_top() {
		console.log('scrolling to top')
		scrolling_to_top.value = true
	}

	onMounted(() => {
		console.log("App mounted")
		// set_location_key(route.params.location_key as string)
		// retrieve_small_location()
		// location_image_link.value = '/assets/uploads/' + location.value.image?.path + '/original' + location.value.image?.ext
		if(player.is_gm) {
			set_dicepool_limit(dicepool_store.dicepool_limit)
		}
	})

	// make sure that new users get redirected to settings
	// or if the location key doesn't make sense
	watch(route, (newRoute) => {
		if(newRoute.name == 'Landing' || ['undefined', 'placeholder'].includes(newRoute.params.location_key as string)) {
			if(player.the_entity?.location?.key && player.the_entity?.location?.key != 'placeholder') {
				router.push({ path: '/location/' + player.the_entity?.location?.key })
			}
			else {
				router.push({ path: '/location/2/settings' })
			}
		}
	})

	onUpdated(() => {
		if(scrolling_to_top.value) {
			app_wrapper_component.value.scrollTo(0, 0)
			scrolling_to_top.value = false
		}
	})

	watch(() => player.the_entity?.location, (newLocation) => {
		// if(newLocation?.image) {
		// 	if(!player.data_saving) {
		// 		location_image_link.value = '/assets/uploads/' + newLocation.image.path + '/original' + newLocation.image?.ext
		// 	}
		// 	else {
		// 		location_image_link.value = '/assets/uploads/' + newLocation.image.path + '/small' + newLocation.image?.ext
		// 	}
		// }
		// set_location_key(route.params.location_key as string)
		// retrieve_small_location()
		// location_image_link.value = '/assets/uploads/' + location.value.image?.path + '/original' + location.value.image?.ext
		if(newLocation?.key && newLocation?.key != route.params.location_key) {
			router.push({ path: '/location/' + newLocation?.key })
		}
	})

	const dicepool_pulsate = ref(false)
	watch(() => dicepool_store.dice.length, () => {
		dicepool_pulsate.value = true
	})
</script>

<template>
	<div id="app-wrapper" :class="[
				{ 'editing': player.editing },
				triptych ? 'triptych' : 'landscape',
				preferredColor,
				player.is_gm ? 'gm' : 'player',
				location_image_link ? 'has-image' : 'no-image',
				view
			]"
			:style="preferredColor == 'dark' ? { 'background-image': 'url(' + location_image_link + ')'} : ''"
			ref="app_wrapper_component">
		<Landscape v-if="player.orientation == 'horizontal'" />
		<Mobile v-else />
	</div>
</template>

<style scoped>
	#app-wrapper {
		height: 100vh;
		overflow: hidden;
		/* overflow-x: hidden;
		overflow-y: scroll; */
		position: relative;
		scroll-behavior: smooth;
		#edit-button, #floating-buttons {
			position: fixed;
		}
		#edit-button {
			top: 2em;
			z-index: 5;
		}
		#floating-buttons {
			font-size: 1.2em;
			top: 4.1em;
			z-index: 1;
			display: flex;
			flex-direction: column;
			input {
				margin-bottom: 0;
				font-size: 1em;
				background-color: var(--color-background-mute);
				text-align: right;
			}
		}
		#content-wrapper {
			height: 100vh;
			.content {
				overflow: auto;
				height: 100vh;
				padding-bottom: v-bind((dicepoolHeight - 3) + 'px');
				/* padding-top: v-bind(header_height + 'px'); */
			}
		}
		/* #current-location {
			top: 0;
			bottom: 0;
			overflow-y: auto;
		} */
		.current-location-transition-enter-active,
		.current-location-transition-leave-active {
			transition: right 0.5s ease;
		}
		.current-location-transition-enter-from,
		.current-location-transition-leave-to {
			right: 100vw;
		}
		.current-location-transition-enter-to,
		.current-location-transition-leave-from {
			right: 0;
		}
		#codex {
			top: 0;
			bottom: 0;
			/* overflow-y: auto; */
		}
		.codex-transition-enter-active,
		.codex-transition-leave-active {
			transition: left 0.5s ease;
		}
		.codex-transition-enter-from,
		.codex-transition-leave-to {
			left: 100vw;
		}
		.codex-transition-enter-to,
		.codex-transition-leave-from {
			left: 0;
		}
	}
	#app-wrapper.editing {
		--color-highlight: blue;
		h1, .header {
			color: var(--color-highlight-heading);
		}
		.panel {
			background-color: var(--color-background-mute);
		}
	}
</style>

<style>
	#app-wrapper {
		height: 100vh;
		overflow-y: scroll;
		overflow-x: hidden;
	}
	.dark.gm {
		--color-highlight: beige;
	}
	.light.gm {
		--color-highlight: midnightblue;
	}

	#app-wrapper.dark {
		/* background-attachment: fixed; */
		background-position: center;
		background-size: cover;

		a {
			text-shadow: none;
		}

		header {
			nav {
				backdrop-filter: blur(5px);
				border-bottom: 1px solid var(--color-border);
				height: 1.4em;

				a {
					text-shadow: #000 0px 0px 2px, #000 0px 0px 4px, #000 0px 0px 8px, #000 0px 0px 2px;
				}

				#character, #perspective {
					text-shadow: none;
					box-shadow: #000 0px 0px 2px, #000 0px 0px 4px, #000 0px 0px 8px, #000 0px 0px 2px;
				}
			}
		}

		.vertical.panel {
			backdrop-filter: blur(5px);
		}

		div#dicepool-footer-container {
			#entity-button {
				color: var(--color-text);
			}
		}

		&.triptych {
			background-size: cover;
			#entity-button {
				box-shadow: inset 0 0 20px var(--color-background);
				text-shadow: #000 0px 0px 2px, #000 0px 0px 4px, #000 0px 0px 8px, #000 0px 0px 2px;
				border-top: 1px solid var(--color-background);
				color: var(--color-text);
			}
			#charactersheet-container, #settings-container, #codex-container {
				backdrop-filter: blur(5px);
			}
		}
		&.landscape {
			/* background-size: contain; */
			#content-wrapper {
				background-color: var(--color-background-mute);
			}
		}
	}

	.light {
		header {
			background-color: var(--color-background);
			border-bottom: 1px solid var(--color-border);
		}
		.panel {
			background-color: var(--color-background-soft);
			backdrop-filter: none;
			&#current-location {
				border-right: 1px solid var(--color-border);
			}
			&#codex {
				border-left: 1px solid var(--color-border);
			}
		}
		#charactersheet-container, #settings-container, #codex-container {
			background-color: var(--color-background);
		}
	}
</style>
