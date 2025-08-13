<script setup lang="ts">
	import { ref, computed, onMounted, watch } from 'vue'
	import type { Ref } from 'vue'
	import { templateRef, useScroll } from '@vueuse/core'

	import { useRoute, useRouter, RouterLink } from 'vue-router'
	
	import { usePlayer } from '@/stores/Player'
	import { useDicepool } from '@/composables/Dicepool'
	import { useSession } from '@/composables/Session'

	import CharacterOverview from '@/views/CharacterOverview.vue'
	import TraitsetOverview from '@/views/TraitsetOverview.vue'
	import TraitsetView from '@/views/TraitsetView.vue'
	import SFXOverview from '@/views/SFXOverview.vue'
	import RulesView from '@/views/RulesView.vue'
	import ToggleButton from '@/components/ToggleButton.vue'

	const props = defineProps({
		orientation: String // 'vertical' or 'horizontal'
	})
	const emit = defineEmits(['show_entity'])
	
	const route = useRoute()
	const router = useRouter()

	const player = usePlayer()
	const { dicepool_limit } = useDicepool()

	const view = ref('settings')

	const {
		get_dicepool_limit,
		set_dicepool_limit
	} = useSession()

	get_dicepool_limit()
	const new_dicepool_limit = ref(dicepool_limit.value)
	watch(dicepool_limit, (newLimit) => {
		new_dicepool_limit.value = newLimit
	})
	function decrease_dicepool_limit() {
		if(dicepool_limit.value <= 0) set_dicepool_limit(0)
		else set_dicepool_limit(dicepool_limit.value - 1)
		get_dicepool_limit()
	}
	function increase_dicepool_limit() {
		set_dicepool_limit(dicepool_limit.value + 1)
		get_dicepool_limit()
	}
	const edit_dicepool_limit_manually = ref(false)
	function update_dicepool_limit() {
		set_dicepool_limit(Number(new_dicepool_limit.value))
		get_dicepool_limit()
		edit_dicepool_limit_manually.value = false
	}

	const player_name: Ref<string> = ref(player.player_name)
	function update_player_name() {
		player.player_name = player_name.value
	}

	const is_gm = computed(() => player.is_gm ? 'gm' : 'player')
	function toggle_gm() {
		player.is_gm = !player.is_gm
	}

	const small_buttons = computed(() => player.small_buttons ? 'small buttons' : 'verbose buttons')
	function toggle_small_buttons() {
		player.small_buttons = !player.small_buttons
	}

	const data_saving = computed(() => player.data_saving ? 'data saving on' : 'data saving off')
	function toggle_data_saving() {
		player.data_saving = !player.data_saving
	}

	// Traitset
	const traitset_key = ref<string|undefined>()
	function switch_to_traitset(key: string) {
		console.log('switching to traitset: ', key)
		view.value = 'traitset'
		router.push({ path: '/location/' + player.the_entity?.location?.key + '/settings/traitset/' + key })
		traitset_key.value = key
	}

	const container = templateRef<HTMLElement>('container')
	const scroll = useScroll(container)

	function go_to(new_view: string) {
		view.value = new_view
		container.value.scrollLeft = 140
		if(new_view == 'location') {
			router.push({ path: '/location/' + player.the_entity?.location?.key })
		}
		else if(new_view == 'settings') {
			router.push({ path: '/location/' + player.the_entity?.location?.key + '/settings' })
		}
		else {
			router.push({ path: '/location/' + player.the_entity?.location?.key + '/settings/' + new_view })
		}
	}

	watch(route, () => {
		if(route.name == 'Landing' && player.the_entity?.location?.key) {
			router.push({ path: '/location/' + player.the_entity?.location.key + '/settings' })
		}
		else if(route.name == 'Landing') {
			router.push({ name: 'Character overview' })
		}
		if(route.matched.length > 2 && route.matched[2].name?.toString().toLowerCase() != view.value) {
			view.value = route.matched[2].name?.toString().toLowerCase() ?? 'settings'
			if(route.params.traitset_key) {
				traitset_key.value = route.params.traitset_key as string
			}
		}
	})
</script>

<template>
	<div id="settings-wrapper" ref="container">
		<div id="settings-container">
			<nav>
				<div class="links">
					
					<div class="link" :class="{ 'header': view == 'location'}" @click="go_to('location')"
							v-if="player.the_entity?.id && player.the_entity.id != 'placeholder'">
						game
					</div>
					
					<div class="link" :class="{ 'header': view == 'settings'}" @click="go_to('settings')">
						settings
					</div>

					<div class="link" :class="{ 'header': view == 'characters'}" @click="go_to('characters')">
						{{ player.is_gm ? 'entities' : 'characters' }}
					</div>

					<div class="link" :class="{ 'header': view == 'traitsets'}" @click="go_to('traitsets')" v-if="player.is_gm">
						traitsets
					</div>

					<div class="link" :class="{ 'header': view == 'sfxs'}" @click="go_to('sfxs')" v-if="player.is_gm">
						sfxs
					</div>

					<div class="link" :class="{ 'header': view == 'rules'}" @click="go_to('rules')">
						help
					</div>

				</div>
			</nav>
			<div class="page" @click="container.scrollLeft = 140">
				<div id="settings" class="setting-page" v-if="view == 'settings'">
					<h1>settings</h1>
					<div id="player-name" class="setting">
						<label for="player_name">player name</label>
						<div id="player-name-input">
							<input id="player_name" type="text" placeholder="player name" v-model="player_name" @blur="update_player_name" />
							<label id="player-name-updated" for="player_name" v-if="player.player_name == player_name">✅</label>
						</div>
					</div>
					<div class="setting">
						<label for="is_gm">role</label>
						<ToggleButton truthy="player" falsy="architect" :default="!player.is_gm" @toggle="toggle_gm" />
					</div>
					<div class="setting">
						<label for="small_buttons">button labels</label>
						<!-- <input id="small_buttons" type="button" class="button" :value="small_buttons" @click="toggle_small_buttons" /> -->
						<ToggleButton truthy="🔘" :falsy="'ℹ\nbutton labels'" :default="player.small_buttons" @toggle="toggle_small_buttons" />
					</div>
					<div class="setting">
						<label for="data_saving">data saving</label>
						<ToggleButton truthy="on" falsy="off" :default="player.data_saving" @toggle="toggle_data_saving" />
					</div>
					<div v-if="player.is_gm" class="setting">
						<label>dicepool limit</label>
						<div id="dicepool-limit">
							<input type="button" class="button" value="-" @click="decrease_dicepool_limit" v-if="!edit_dicepool_limit_manually" />

							<span class="dicepool-limit" @click="edit_dicepool_limit_manually = true; new_dicepool_limit = dicepool_limit" v-if="!edit_dicepool_limit_manually">
								{{ dicepool_limit && dicepool_limit > 0 ? dicepool_limit : '∞' }}
							</span>
							<input class="dicepool-limit" type="text" v-model="new_dicepool_limit" v-if="edit_dicepool_limit_manually" />
							<input type="button" class="button" value="ok" @click="update_dicepool_limit" v-if="edit_dicepool_limit_manually && dicepool_limit != new_dicepool_limit" />
							<input type="button" class="button" value="x" @click="edit_dicepool_limit_manually = false" v-if="edit_dicepool_limit_manually" />

							<input type="button" class="button" value="+" @click="increase_dicepool_limit" v-if="!edit_dicepool_limit_manually" />
						</div>
					</div>
				</div>
				<CharacterOverview class="setting-page" v-if="view == 'characters'" @show_entity="emit('show_entity', $event)" />
				<!-- <LocationOverview v-if="view == 'locations'" /> -->
				<TraitsetOverview class="setting-page" v-if="view == 'traitsets' || (view == 'traitset' && props.orientation == 'horizontal')" @show_traitset="switch_to_traitset" />
				<TraitsetView class="setting-page" v-if="traitset_key && view == 'traitset'" :traitset_key="traitset_key" />
				<SFXOverview class="setting-page" v-if="view == 'sfxs'" />
				<RulesView class="setting-page" v-if="view == 'rules'" />
			</div>
		</div>
		<div class="button menu-button"
				:class="{ 'active': scroll.x.value > 0}"
				@click="scroll.x.value > 0 ? container.scrollTo(0, 0) : container.scrollTo(300, 0)"
				v-if="player.orientation == 'vertical'">
			<span class="icon">
				{{scroll.x.value > 0 ? '➡' : '⬅'}}
			</span>
			<span class="label" v-if="!player.small_buttons">
				menu
			</span>
		</div>
		<!-- <div class="bottom-scroll-space scroll-space"></div> -->
	</div>
</template>

<style scoped>
	#settings-wrapper {
		/* position: relative; */
		#settings-container {
			/* width: fit-content; */
			height: 100vh;
			text-align: center;
			display: flex;
			nav, .page {
				height: 100%;
				scroll-snap-align: start;
			}
			nav {
				flex: 0 0 140px;
				height: 100vh;
				.links {
					padding-top: 3em;
					display: flex;
					flex-direction: column;
					width: 100%;
					gap: 1em;
					.link {
						color: var(--color-highlight-text);
						font-size: 1.2em;
						cursor: pointer;
						padding: 0.5em;
					}
				}
			}
			.page {
				padding-bottom: 5em;
				display: flex;
				#settings {
					display: flex;
					flex-direction: column;
					justify-content: center;
					align-items: center;
					gap: 2em;
					.setting {
						width: 100%;
						display: flex;
						flex-direction: column;
						align-items: center;
						&#player-name {
							#player-name-input {
								width: 80%;
								position: relative;
								#player_name {
									/* display: block; */
									width: 100%;
									font-size: 2em;
									text-align: center;
									border: none;
									border-bottom: 1px solid var(--color-border);
									background-color: var(--color-background);
									color: var(--color-text);
								}
								#player-name-updated {
									position: absolute;
									right: 10px;
									top: 50%;
									transform: translateY(-50%);
								}
							}
						}
						#dicepool-limit {
							width: 50%;
							min-width: 150px;
							display: flex;
							justify-content: space-evenly;
							.dicepool-limit {
								font-size: 2em;
								max-width: 50px;
							}
						}
					}
				}
				.setting-page {
					height: 100vh;
					overflow-y: auto;
					flex-grow: 1;
				}
			}
		}
		.menu-button {
			position: absolute;
			top: 0;
			left: 140px;
			margin: 0;
			width: 3em;
			border-radius: 0 0 10px 0;
			border-right: none;
			display: flex;
			flex-direction: column;
			align-items: center;
			gap: 0.5em;
			.icon {
				font-size: 1.6em;
			}
			.label {
				font-size: 1em;
				transform: rotate(-90deg);
				margin-bottom: 1em;
			}
		}
	}
	.bottom-scroll-space {
		height: 200px;
	}
</style>

<style>
.triptych #settings-wrapper {
	width: 100vw;
	overflow-x: scroll;
	scroll-snap-type: x mandatory;
	scroll-behavior: smooth;
	overflow-y: hidden;
	height: 100vh;
	position: relative;
	.page {
		flex: 0 0 100vw;
		.setting-page {
			width: 100vw;
		}
	}
}
.landscape #settings-wrapper {
	.page {
		/* flex: 0 0 33vw; */
		/* padding-top: 4em; */
		width: calc(100vw - 140px);
		justify-content: center;
		gap: 1em;
		padding: 0 1em;
		.setting-page {
			min-width: 20vw;
			/* max-width: 50vw; */
		}
	}
}
.dark #settings-wrapper {
	backdrop-filter: blur(5px);
	.page {
		text-shadow: var(--text-shadow);
	}
	nav {
		background-image: linear-gradient(
			to left,
			var(--color-background-mute) 0,
			var(--color-background-mute) 90%,
			var(--color-background)
		);
		.links {
			.link {
				background-image: linear-gradient(
					to left,
					var(--color-highlight) 0,
					var(--color-highlight) 90%,
					var(--color-background-mute)
				);
			}
		}
	}
}
.light #settings-wrapper {
	nav {
		background-color: var(--color-background-soft);
		border-left: 1px solid var(--color-border);
		.links {
			.link {
				background-color: var(--color-highlight);
			}
		}
	}
}
</style>
