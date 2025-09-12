<script setup lang="ts">
	import { ref, watch } from 'vue';
	import { useRoute, useRouter } from 'vue-router';

	import { usePlayer } from '@/stores/Player';
	import { useDicepoolStore } from '@/stores/DicepoolStore';

	import CurrentLocationView from '@/views/CurrentLocationView.vue';
	import CharacterView from '@/views/CharacterView.vue';
	import SettingsView from '@/views/SettingsView.vue';
	import CodexView from '@/views/CodexView.vue';
	import DicepoolView from '@/views/DicepoolView.vue';

	import { entity_icons } from '@/composables/Entity'
	import { die_constants } from '@/composables/Die'

	const route = useRoute()
	const router = useRouter()
	const player = usePlayer()
	const dicepool_store = useDicepoolStore()

	const mobile_component = ref<HTMLDivElement>()
	const view = ref('location')

	const overwrite_entity_key = ref<string>()
	const dicepool_expanded = ref(false)
	const dicepool_pulsate = ref(false)

	function show_entity(entity_key: string) {
		overwrite_entity_key.value = entity_key
		view.value = 'entity'
		router.push({ path: '/location/' + player.the_entity?.location?.key + '/entity/' + entity_key })
	}

	function click_location() {
		overwrite_entity_key.value = undefined
		if(view.value == 'location') {
			scroll_top()
		}
		else {
			view.value = 'location'
		}
		router.push({ path: '/location/' + player.the_entity?.location?.key })
	}
	
	function click_entity() {
		if(view.value == 'entity') {
			if(overwrite_entity_key.value) {
				overwrite_entity_key.value = undefined
				router.push({ path: '/location/' + player.the_entity?.location?.key + '/entity/' + player.the_entity?.key })
			}
			else {
				view.value = 'location'
				router.push({ path: '/location/' + player.the_entity?.location?.key })
			}
		}
		else {
			view.value = 'entity'
			router.push({ path: '/location/' + player.the_entity?.location?.key + '/entity/' + (overwrite_entity_key.value ?? player.the_entity?.key) })
		}
	}

	function take_gm_perspective() {
		if(player.is_gm) {
			player.set_perspective_id('Entities/1')
			player.retrieve_perspective()
		}
	}

	function click_settings() {
		overwrite_entity_key.value = undefined
		if(view.value == 'settings') {
			view.value = 'location'
			router.push({ path: '/location/' + player.the_entity?.location?.key })
		}
		else {
			view.value = 'settings'
			router.push({ path: '/location/' + player.the_entity?.location?.key + '/settings' })
		}
	}

	function click_codex() {
		overwrite_entity_key.value = undefined
		if(view.value == 'contacts') {
			view.value = 'location'
			router.push({ path: '/location/' + player.the_entity?.location?.key })
		}
		else {
			view.value = 'contacts'
			router.push({ path: '/location/' + player.the_entity?.location?.key + '/contacts' })
		}
	}

	function scroll_top() {
		if(mobile_component.value) {
			mobile_component.value.scrollTo(0, 0)
		}
	}

	watch(route, () => {
		if(route.matched.length == 1 && route.matched[0].name?.toString().toLowerCase() && route.matched[0].name?.toString().toLowerCase() != view.value) {
			console.log('switching to ' + route.matched[0].name?.toString().toLowerCase())
			view.value = route.matched[0].name?.toString().toLowerCase()
		}
		else if(route.matched.length > 1 && route.matched[1].name?.toString().toLowerCase() && route.matched[1].name?.toString().toLowerCase() != view.value) {
			console.log('switching to ' + route.matched[1].name?.toString().toLowerCase())
			view.value = route.matched[1].name?.toString().toLowerCase()
		}
	})

	watch(() => player.the_entity?.location, (newLocation) => {
		if(route.params.location_key != newLocation?.key) {
			router.push({ path: '/location/' + newLocation?.key })
		}
	})
</script>

<template>
	<div id="mobile-container" ref="mobile_component">

		<div id="location-container" v-if="view == 'location'" :key="view">
			<CurrentLocationView
				:location_key="route.params.location_key as string ?? player.the_entity?.location?.key ?? ''"
				:key="route.params.location_key as string ?? player.the_entity?.location?.key ?? ''"
				@show_entity="show_entity"
				@transverse="scroll_top" />
		</div>

		<div id="charactersheet-container" v-if="view == 'entity'" :key="view">
			<CharacterView
				:entity_key="overwrite_entity_key ?? player.the_entity?.key"
				:key="overwrite_entity_key ?? player.the_entity?.key"
				orientation="vertical" />
		</div>
		<div id="settings-container" v-if="view === 'settings'" :key="view">
			<SettingsView orientation="vertical" @show_entity="show_entity" />
		</div>
		<div id="codex-container" v-if="view == 'contacts'" :key="view">
			<CodexView id="codex"
				:shown="view == 'contacts'"
				@hide_codex="view = 'location'"
				@show_entity="show_entity" />
		</div>

		<footer id="mobile-footer">
			<nav v-if="!dicepool_expanded">
				<div id="left-footer-links">
					<a class="footer-button" :class="{'active': view == 'location'}"
							@click="click_location">
						<span class="icon">🗺</span>
						<span v-if="!player.small_buttons">
							{{ 'location' }}
						</span>
					</a>
					<a id="entity-button" class="footer-button"
							:class="[
								{'active': route.name == 'Entity' && route.params.entity_key == player.the_entity?.key},
								{'with-image': player.is_gm && player.the_entity?.image}
							]"
							:style="player.is_gm ? {
								backgroundImage: `url('/assets/uploads/${player.the_entity?.image?.path}/small${player.the_entity?.image?.ext}`
							} : null"
							@click="click_entity"
							@click.right="take_gm_perspective"
							v-touch:hold="take_gm_perspective"
							@contextmenu="(e) => e.preventDefault()">
						<span class="icon" v-if="!(player.is_gm && player.the_entity?.image)">
							{{ entity_icons[(player.the_entity?.entityType ?? 'empty')] }}
						</span>
						<span v-if="!player.small_buttons || (player.is_gm && !player.the_entity?.image)">
							{{ player.the_entity?.name }}
						</span>
					</a>
				</div>
				<div id="dicepool-footer-container">
					<div id="dicepool-footer-widget" @click="dicepool_expanded = true"
							:class="[
								{ 'pulsate': dicepool_pulsate },
								{ 'active': dicepool_store.dice.length > 0 }
							]"
							@animationend="dicepool_pulsate = false">
						<div id="dicepool-footer-widget-count"
								class="header"
								v-if="dicepool_store.dice.length > 5">
							{{ dicepool_store.dice.length }}
						</div>
						<div id="dicepool-footer-widget-count" class="icon"
								v-else-if="dicepool_store.dice.length == 0">
							🎲
						</div>
						<div id="dicepool-footer-widget-geometry" v-else>
							<span v-for="(d, i) of dicepool_store.dice" :key="d.id"
									class="geometry-point"
									:class="dicepool_store.dice.length == 5 ? 'pentagram-' + i
										: dicepool_store.dice.length == 4 ? 'square-' + i
										: dicepool_store.dice.length == 3 ? 'triangle-' + i
										: dicepool_store.dice.length == 2 ? 'pair-' + i
										: 'single'">
								{{ die_constants.find(dc => dc.rating == d.rating)?.active }}
							</span>
						</div>
					</div>
				</div>
				<div id="right-footer-links">
					<a class="footer-button"
							:class="{'active':
								['Settings', 'Traitset overview', 'Traitsets'].includes(route.name as string)
								&& view != 'contacts' && view != 'location'}"
							@click="click_settings">
						<span class="icon">☰</span>
						<span v-if="!player.small_buttons">
							{{ 'settings' }}
						</span>
					</a>
					<a class="footer-button" :class="{'active': view == 'contacts'}"
							@click="click_codex">
						<span class="icon">🗂</span>
						<span v-if="!player.small_buttons">
							{{ 'contacts' }}
						</span>
					</a>
				</div>
			</nav>
			<div id="dicepool-container" v-if="dicepool_expanded">
				<DicepoolView id="dicepool" ref="dicepool"
					:expanded="dicepool_expanded"
					@expand="dicepool_expanded = true"
					@collapse="dicepool_expanded = false" />
			</div>
		</footer>
	</div>
</template>

<style scoped>
#mobile-container {
	/* mobile */
	background-position: center top;
	background-size: cover;
	z-index: 1;
	header {
		z-index: 5;
	}
	.panel {
		/* width: 100vw; */
		overflow-x: hidden;
		/* overflow-y: auto; */
		position: fixed;
		z-index: 5;
	}
	/* #content {
		max-height: 100vh;
	} */
	#edit-button, #floating-buttons {
		right: 6px;
		font-size: 1.2em;
	}
	footer {
		position: fixed;
		bottom: 0;
		z-index: 3;
		nav {
			z-index: 5;
			position: fixed;
			bottom: 0;
			left: 0;
			right: 0;
			/* height: 50px; */
			display: flex;
			justify-content: space-around;
			align-items: flex-end;
			/* padding: 0 10px; */
			/* box-shadow: 0 -2px 10px rgba(0,0,0,0.2); */
			transition: transform 0.3s ease;
			.icon {
				font-size: 1.6em;
			}
			div#left-footer-links, div#right-footer-links {
				flex: 1;
				display: flex;
				/* flex-direction: column; */
				/* align-items: center; */
				justify-content: center;
				font-size: 12px;
				/* padding: 8px 5px; */
				/* border: none; */
				/* border-top: 1px solid var(--color-border); */
				cursor: pointer;
				a.footer-button {
					border-top: 1px solid var(--color-border);
					background-color: var(--color-background);
					color: var(--color-text);
					width: 100%;
					height: 4em;
					display: flex;
					flex-direction: column;
					justify-content: end;
					align-items: center;
					text-align: center;
					line-height: 1.5em;
					text-wrap: nowrap;
					&.active {
						background-color: var(--color-highlight);
						color: var(--color-highlight-text);
					}
					&#entity-button {
						background-position: center 20%;
						background-size: cover;
					}
				}
			}
			div#dicepool-footer-container {
				position: relative;
				width: 70px;
				height: 70px;
				margin: 0 5px;
				div#dicepool-footer-widget {
					position: absolute;
					top: 0;
					left: 50%;
					transform: translateX(-50%);
					width: 100px;
					height: 100px;
					border-radius: 50%;
					/* border: none; */
					border: 1px solid var(--color-border);
					&.active {
						background-color: var(--color-highlight);
						color: var(--color-highlight-text);
					}
					background-color: var(--color-background);
					color: var(--color-text);
					box-shadow: 0 3px 10px rgba(0,0,0,0.3);
					font-weight: bold;
					font-size: 20px;
					cursor: pointer;
					display: flex;
					align-items: baseline;
					justify-content: center;
					div#dicepool-footer-widget-count {
						display: flex;
						align-items: center;
						justify-content: center;
						position: absolute;
						height: 50px;
						width: 50px;
						bottom: 35%;
						left: 50%;
						transform: translateX(-50%);
						&.header {
							font-size: 2em;
						}
					}
					div#dicepool-footer-widget-geometry {
						display: flex;
						align-items: end;
						justify-content: center;
						height: 50px;
						width: 50px;
						top: 15px;
						/* background-color: var(--color-background-mute); */
						position: relative;
						.geometry-point {
							position: absolute;
							display: flex;
							align-items: center;
							justify-content: center;
							transform: translate(-50%, -50%);
						}
						.pentagram-0 { top: 0%; left: 50% }
						.pentagram-1 { top: 33%; left: 93%; }
						.pentagram-2 { top: 80%; left: 75%; }
						.pentagram-3 { top: 80%; left: 25% }
						.pentagram-4 { top: 33%; left: 7%; }
						.square-0 { top: 0%; left: 50% }
						.square-1 { top: 40%; left: 90%; }
						.square-2 { top: 80%; left: 50%; }
						.square-3 { top: 40%; left: 10%; }
						.triangle-0 { top: 10%; left: 50% }
						.triangle-1 { top: 70%; left: 10%; }
						.triangle-2 { top: 70%; left: 90%; }
						.pair-0 { top: 50%; left: 10% }
						.pair-1 { top: 50%; left: 90% }
						.single { top: 50%; left: 50% }
					}
				}
			}
		}
		#dicepool {
			position: fixed;
			width: 100vw;
			top: v-bind(windowHeight - dicepoolHeight + 2 + 'px');
		}
	}
	#charactersheet-container, #settings-container, #codex-container {
		height: 100vh;
		width: 100vw;
		z-index: 2;
		overflow-x: hidden;
		overflow-y: auto;
		scroll-behavior: smooth;
		position: fixed;
		top: 0;
	}
	#dicepool-container {
		position: fixed;
		bottom: 0;
		display: flex;
		justify-content: center;
		height: 0;
		width: 100vw;
		overflow: visible;
		z-index: 10;
		#dicepool {
			position: absolute;
			bottom: -1px;
		}
	}
}
</style>
