<script setup lang="ts">
	import { ref, watch, computed, defineAsyncComponent, onMounted } from 'vue'
	import _ from 'lodash'
	import { useVibrate, usePreferredColorScheme } from '@vueuse/core'

	import SessionControl from '@/components/SessionControl.vue'
	import PoolEntity from '@/components/PoolEntity.vue'
	import Die from '@/components/Die.vue'
	import DiePicker from '@/components/DiePicker.vue'
	import PoolPlayer from '@/components/PoolPlayer.vue'
	import SuggestedComplication from '@/components/SuggestedComplication.vue'
	const DieComponent = defineAsyncComponent(() => import('@/components/Die.vue'))
	
	import { useDicepool } from '@/composables/Dicepool'
	import { useDicepoolWS } from '@/composables/DicepoolWS'
	import { die_shapes } from '@/composables/Die'

	import { useDicepoolStore } from '@/stores/DicepoolStore'
	import { usePlayerStore } from '@/stores/PlayerStore'

	import type { Die as DieType } from '@/interfaces/Types'
	import ResolutionSWADE from '@/components/ResolutionSWADE.vue'

	const props = defineProps<{
		expanded: boolean
	}>()

	const emit = defineEmits([
		'expand',
		'collapse'
	])

	const player = usePlayerStore()
	const dicepoolStore = useDicepoolStore()
	const websocket = useDicepoolWS()

	console.log("connecting websocket")
	onMounted(() => {
		console.log("mounted dicepool")
		websocket.connect()
	})

	const dicepool = useDicepool(true)

	const held = ref(false)

	const { vibrate } = useVibrate({ pattern: [20] })
	const preferredColor = usePreferredColorScheme()
	const ruleset_logo = computed(() => {
		return dicepoolStore.dice.length <= 2 ? 'SwadeLogoSmall' : 'CPC-' + preferredColor.value
	})

	const editing = ref(false)
	const editing_die = ref<DieType>()
	
	watch(() => props.expanded, (newExpanded) => {
		if(newExpanded == true) {
			// verbose_dice.value = false
			dicepool.pullInterval.value = 3000
			dicepool.pull_dicepools()
		}
		else {
			editing.value = false
			dicepool.pullInterval.value = 20000
		}
	})

	function hide_dicepool() {
		emit('collapse')
	}

	const verbose_dice = ref(true)

	function open_dicepool() {
		emit('expand')
	}

	// console.log("starting dicepool polling")
	// dicepool.pull_clock()

	// const time_until_next_poll = computed(() => {
	// 	return dicepool.pullInterval.value - (Date.now() - dicepool.last_poll_timestamp.value)
	// })

	// const css_pull_timer = computed<number>(() => {
	// 	// uses dicepool.pullInterval and dicepool.time_until_next_poll to determine the pull timer
	// 	// returns percentile
	// 	return time_until_next_poll.value / dicepool.pullInterval.value * 100
	// })

	dicepool.pull_clock()
	const polling = ref(true)
	const time_until_next_poll = ref(0)
	const time_until_next_poll_percentile = computed(() => {
		return time_until_next_poll.value / dicepool.pullInterval.value * 100
	})
	function poll() {
		if(polling) {
			time_until_next_poll.value = dicepool.pullInterval.value - (Date.now() - dicepool.last_poll_timestamp.value)
		}
		setTimeout(poll, 1500)
	}
	poll()

	function click_die(die: DieType) {
		if(!held.value) {
			if(!player.editing) {
				if(dicepool.inAddingPhase.value) {
					dicepool.remove_die(die)
				}
				if(dicepool.inResultPhase.value) {
					dicepool.toggle_result(die)
					result_pulsate.value = true
					if(dicepool.result_size.value == dicepool.result_limit.value) {
						set()
					}
				}
				if(dicepool.inEffectPhase.value && !die.isResultDie) {
					dicepool.toggle_effect(die)
					effect_pulsate.value = true
				}
			}
			else {
				editing.value = true
				editing_die.value = die
			}
		}
	}

	function longtap_die(d: DieType) {
		held.value = true
		editing.value = true
		editing_die.value = d
		vibrate()
		setTimeout(() => held.value = false, 500)
	}

	function edit_die(rating?: DieType[]) {
		if(editing_die.value && rating) {
			dicepool.remove_die(editing_die.value)
			editing_die.value = undefined
		}
		dicepool.add_dice(rating ?? [])
		editing.value = false
	}

	function add_custom_dice(rating: DieType[]) {
		dicepool.add_dice(rating)
	}

	function click_complication(complication?: string) {
		dicepoolStore.suggested_complications
			.filter(d => d.traitsettingId == complication)
			.forEach(d => {
				dicepool.add_die(d)
				if(d.ratingType == 'resource') {
					dicepool.change_result_limit(1)
				}
			})
		// dicepool.add_dice(
		// 	dicepoolStore.suggested_complications
		// 		.filter(d => d.traitsettingId == complication)
		// )
	}

	function click_complication_die(die: DieType) {
		dicepool.add_die(die)
		if(die.ratingType == 'resource') {
			dicepool.change_result_limit(1)
		}
	}

	function set() {
		if(dicepool.inResultPhase.value) {
			dicepool.next()
		}
		else if(dicepool.inEffectPhase.value) {
			dicepool.next()
			dicepool.push_dicepool()
		}
	}

	function reset() {
		dicepool.clear_dicepool()
		hide_dicepool()
	}

	const title_pulsate = ref(false)
	watch(dicepool.dicepool_size, (newSize) => {
		title_pulsate.value = true
		if(newSize == 0 && props.expanded) {
			hide_dicepool()
		}
	})
	const phase_pulsate = ref(false)
	watch(() => dicepoolStore.phase, () => {
		phase_pulsate.value = true
	})
	const result_pulsate = ref(false)
	const effect_pulsate = ref(false)
</script>

<template>
	<div id="dicepool"
			:class="[
				props.expanded ? 'expanded' : 'collapsed',
				{ 'empty': dicepool.dicepool_size.value == 0 }
			]"
			@contextmenu="(e) => e.preventDefault()">
		<div id="dicepool-wrapper">
			<div class="title"
					:class="{ 'pulsate': title_pulsate }"
					@animationend="title_pulsate = false"
					@click.stop="props.expanded ? hide_dicepool() : open_dicepool()">
				<div id="dicepool-limit" v-if="
						(dicepoolStore.dicepool_limit && dicepoolStore.dicepool_limit > 0 && dicepool.dicepool_size.value <= dicepoolStore.dicepool_limit)
						|| (dicepool.dicepool_size.value > 0 && (!dicepoolStore.dicepool_limit || dicepoolStore.dicepool_limit <= 0))">
					<input type="button" id="decrease-dicepool-limit" class="button-mnml"
						:value="player.small_buttons ? '⊖' : 'decrease limit ⊖'"
						@click.stop="dicepool.change_dicepool_limit(-1)"
						v-if="dicepoolStore.dicepool_limit && dicepoolStore.dicepool_limit > 0" />
					<div id="dicepool-size">
						<span v-for="d of dicepoolStore.dice">
							{{ die_shapes[d.rating + '_active'] }}
						</span>
						<span v-for="i in dicepool.dicepool_limit.value - dicepool.dicepool_size.value"
							v-if="dicepoolStore.dicepool_limit && dicepoolStore.dicepool_limit > 0">
							{{ die_shapes.default_inactive }}
						</span>
					</div>
					<input type="button" id="increase-dicepool-limit" class="button-mnml"
						:value="player.small_buttons ? '⊕' : '⊕ increase limit'"
						@click.stop="dicepool.change_dicepool_limit(1)"
						v-if="dicepoolStore.dicepool_limit && dicepoolStore.dicepool_limit > 0" />
				</div>
				<div id="dicepool-title" v-else-if="!props.expanded">
					DICE TRAY
				</div>
				<div id="dicepool-title" class="header" v-else>
					{{ dicepoolStore.phase.toString() }}
				</div>
			</div>
			<div id="poll-timer-wrapper">
				<div id="poll-timer">{{ time_until_next_poll }}ms</div>
			</div>
			<div id="dicepool-collapsible" v-if="props.expanded">
				<div id="dicepool-inner">
					<!-- <input type="button" class="button-mnml" id="dicepool-details-view"
						:value="verbose_dice ?
							player.small_buttons ? '👁' : '👁 detail view' :
							player.small_buttons ? '🔘' : '🔘 simple view'"
						@click.stop="verbose_dice = !verbose_dice" /> -->
					<SessionControl v-if="player.is_gm" />





					<input type="button" @click="websocket.engage" value="engage" />






					<div id="dicepools" :style="{ 'background-image': dicepool.dicepool_size.value > 0 ? `url('/img/` + ruleset_logo + `.png')` : '' }">

						<div id="dicepool-picker" v-if="dicepool.inResultPhase.value || dicepool.inEffectPhase.value">

							<span class="info-half result" :class="[{ 'active': dicepool.inResultPhase.value }, { 'pulsate': result_pulsate }]"
									@click.stop="dicepool.set_result_phase()"
									@animationend="result_pulsate = false">
								<div class="header">result{{ ': ' + dicepool.result.value }}</div>
								<div class="info-half-wrapper">
									<input type="button" class="button-mnml" value="-"
										@click.stop="dicepool.change_result_limit(-1, undefined, true)"
										v-if="dicepool.result_limit.value > 1 && dicepool.inResultPhase.value" />
									<div id="result-dice">
										<Die
											v-for="die in dicepoolStore.dice.filter((d) => d.isResultDie && d.ratingType != 'resource')" :key="die.id"
											:die="die"
											in_pool
											:is_choice="dicepool.inResultPhase.value"
											@click.stop="dicepool.inResultPhase.value ? die.isResultDie = false : dicepool.set_result_phase()" />
									</div>
									<span class="slot" v-for="i of dicepool.result_limit.value - dicepool.result_size.value" :key="i">
										{{ die_shapes.default_inactive }}
									</span>
									<input type="button" class="button-mnml" value="+"
										@click.stop="dicepool.change_result_limit(1, undefined, true)"
										v-if="dicepool.inResultPhase.value" />
								</div>
							</span>

							<span class="info-half effect" :class="[{ 'active': dicepool.inEffectPhase.value }, { 'pulsate': effect_pulsate }]"
									@click.stop="dicepool.set_effect_phase()"
									@animationend="effect_pulsate = false">
								<div class="header">effect</div>
								<div class="info-half-wrapper">
									<input type="button" class="button-mnml" value="-" @click.stop="dicepool.change_effect_limit(-1)"
										v-if="dicepool.effect_limit.value > 1 && dicepool.inEffectPhase.value" />
									<div id="effect-dice">
										<Die v-for="die in dicepoolStore.dice.filter((d) => d.isEffectDie)"
											:die="die"
											in_pool
											@click.stop="dicepool.inEffectPhase.value ? die.isEffectDie = false : dicepool.set_effect_phase()" />
									</div>
									<span class="slot" v-for="i of dicepool.effect_limit.value - dicepool.effect_size.value" :key="i">
										{{ die_shapes.default_inactive }}
									</span>
									<input type="button" class="button-mnml" value="+" @click.stop="dicepool.change_effect_limit(1)"
										v-if="dicepool.inEffectPhase.value" />
								</div>
							</span>

						</div>

						<ResolutionSWADE v-if="dicepool.inSwadeResultPhase.value && dicepoolStore.dice[0].result" />

						<div id="pool-dice">
							<div id="gm-die-picker" v-if="dicepool.inAddingPhase.value && !editing_die">
								<DiePicker @change-die="add_custom_dice" custom />
							</div>

							<div id="the-meat"
									v-if="!dicepool.inResolvePhase.value">
								<div id="chosen-dice">
									<div id="chosen-dice-wrapper">
										<div id="verbose-dice" v-if="verbose_dice">
											<PoolEntity
												v-for="entity in new Set(dicepoolStore.dice.map(d => d.entityId)).values()" :key="entity"
												:entity_id="entity ?? ''"
												:dice="dicepoolStore.dice.filter(d => d.entityId == entity)"
												:result_limit="dicepool.result_limit.value"
												:effect_limit="dicepool.effect_limit.value"
												@longpress_die="(die: DieType) => longtap_die(die)" />
										</div>
										<div id="simple-dice" v-else>
											<div id="average-result" v-if="dicepoolStore.dice.length > 0">
												{{ (dicepoolStore.dice.map((d) => d.sides).reduce((acc, curr) => acc + (curr / 2), 0) / dicepoolStore.dice.length ) * dicepool.result_limit.value }}
											</div>
											<template v-for="die in dicepool.interactive_dice.value" :key="die.id">
												<DieComponent
													v-if="die.id != editing_die?.id"
													:class="{ 'editing': editing_die && die.id == editing_die.id }"
													:die="die"
													size="5em"
													is_choice
													in_pool
													v-touch:hold="()=>longtap_die(die)"
													@click.stop="()=>click_die(die)"
													@click.right="()=>longtap_die(die)"
													@contextmenu.prevent="(e) => e.preventDefault()" />
												<DiePicker
													v-if="die.id == editing_die?.id"
													radial
													size="5em"
													@change-die="(r) => edit_die(r)"
													:die="editing_die"
													@cancel="editing_die = undefined; editing = false" show_effects :custom="false" />
											</template>
										</div>
									</div>
								</div>
								<div id="edit-die" v-if="editing && verbose_dice">
									<DiePicker
										@change-die="(r) => edit_die(r)"
										:die="editing_die"
										@cancel="editing_die = undefined; editing = false" show_effects :custom="false" />
								</div>
								<div id="suggested-complications" v-if="dicepool.inAddingPhase.value">
									<template v-for="complication in new Set(dicepoolStore.suggested_complications.map(d => d.traitsettingId)).values()"
											:key="complication">
										<SuggestedComplication
											:complication="dicepoolStore.suggested_complications.filter(d => d.traitsettingId == complication)"
											@click_complication="click_complication(complication)"
											@click_die="click_complication_die"
											v-if="dicepoolStore.suggested_complications.filter(d => d.traitsettingId == complication).length > 0" />
									</template>
								</div>
							</div>

						</div>
						<div id="opposing-pools">
							<PoolPlayer
								v-for="opposing_pool in dicepoolStore.resolutions.filter(r => r.player.uuid != player.uuid || dicepool.inResolvePhase.value)"
								:key="opposing_pool.player.uuid"
								:resolution="opposing_pool" />
						</div>
					</div>
				</div>
				<div id="buttons" :class="[dicepoolStore.dice.length < 3 ? 'empty-dicepool' : 'dicepool-presence', dicepoolStore.resolutions.length == 0 ? '' : '']">
					<button id="btn_roll" @click.stop="dicepool.roll" class="dicepool-button" v-if="dicepool.inAddingPhase.value">
						roll {{ dicepoolStore.dice.length <= 2 ? 'SWADE' : 'Cortex' }}
					</button>
					<button id="btn_set" @click.stop="set" class="dicepool-button" v-if="dicepool.inResultPhase.value || dicepool.inEffectPhase.value">set</button>
					<button id="btn_reset" @click.stop="reset" class="dicepool-button">empty dicepool</button>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
	#dicepool {
		z-index: 5;
		display: flex;
		flex-direction: column;
		align-items: center;
		min-height: 40px;
		max-height: 90vh;
		#dicepool-wrapper {
			min-width: 33vw;
			.title {
				font-weight: 500;
				color: var(--color-background);
				border-top: 1px solid var(--color-border);
				cursor: pointer;
				height: 40px;
				#dicepool-title {
					display: flex;
					justify-content: center;
					align-items: center;
					height: 100%;
				}
				#dicepool-limit {
					display: flex;
					justify-content: space-between;
					align-items: center;
					height: 100%;
					gap: 1em;
					#dicepool-size {
						display: flex;
						justify-content: space-evenly;
						align-items: center;
						flex-grow: 1;
						span {
							display: block;
							flex-grow: 1;
							text-align: center;
						}
					}
					.button-mnml {
						background-color: transparent;
						padding: .5em 1em;
						margin: 0;
						line-height: 0;
						border: none;
					}
				}
				&:hover {
					background-color: var(--color-highlight-mute);
				}
			}
			#poll-timer-wrapper {
				background-color: var(--color-border);
				#poll-timer {
					width: v-bind(time_until_next_poll_percentile + '%');
					height: 4px;
					background-color: var(--color-highlight);
					transition: width 1.5s;
				}
			}
			#dicepool-collapsible {
				background-color: var(--color-background-mute);
				backdrop-filter: blur(5px);
				/* overflow-y: auto; */
				#dicepool-inner {
					max-height: calc(90vh - 40px - 3em);
					/* overflow: hidden; */
					overflow-y: auto;
					#playing {
						text-align: center;
						background-color: var(--color-background);
						/* color: var(--color-); */
						border-bottom: 1px solid var(--color-border);
						font-size: 1.5em;
						padding: 0 .4em;
						float: right;
						margin: .2em;
						border-radius: 20%;
						z-index: 10;
						position: relative;
						&.active {
							color: var(--color-highlight);
						}
					}
					#dicepools {
						position: relative;
						background-repeat: no-repeat;
						background-position: calc(100% - 20px) calc(100% - 20px);
						background-size: min(200px, 20vw);
						#dicepool-picker {
							display: flex;
							.info-half {
								/* width: 50%; */
								/* height: 100px; */
								border: 1px solid var(--color-border);
								margin: 10px;
								display: flex;
								flex-direction: column;
								justify-content: space-evenly;
								flex-grow: 1;
								.info-half-wrapper{
									display: flex;
									justify-content: space-evenly;
									align-items: center;
									.slot, .button-mnml {
										font-size: 2em;
									}
									#result-dice, #effect-dice {
										display: flex;
										flex-wrap: wrap;
									}
								}
								&.active {
									border: 1px solid var(--color-highlight);
								}
							}
						}
						#pool-dice {
							display: flex;
							#gm-die-picker {
								width: 48px;
								border-right: 1px solid var(--color-border);
							}
							#the-meat {
								flex-grow: 1;
								display: flex;
								flex-direction: column;
								justify-content: space-around;
								background-size: 20%;
								background-repeat: no-repeat;
								background-position: right 20px bottom 20px;
								#dicepool-details-view {
									float: left;
								}
								#chosen-dice {
									position: relative;
									height: 100%;
									padding: 1em;
									line-height: 1em;
									#chosen-dice-wrapper {
										/* display: flex;
										flex-wrap: wrap;
										justify-content: center;
										align-items: center;
										gap: .4em; */
										height: 100%;
										max-height: 60vh;
										overflow-y: auto;
									}
									.die.editing {
										border: 1px solid red;
									}
									#button-verbose {
										position: absolute;
										top: 10px;
										right: 10px;
										z-index: 1;
									}
									#simple-dice {
										display: flex;
										flex-wrap: wrap;
										justify-content: space-evenly;
										align-items: space-evenly;
										max-width: 200px;
										width: 100%;
										height: 100%;
										.die {
											margin: .4em;
											cursor: crosshair;
										}
									}
								}
								#suggested-complications {
									display: flex;
									flex-wrap: wrap;
								}
							}
						}
					}
					#opposing-pools {
						display: flex;
						justify-content: space-around;
						gap: .4em;
					}
				}
			}
			#buttons {
				width: 100%;
				height: 3em;
				.dicepool-button {
					border: none;
					padding: .5em;
					font-size: 1.2em;
					width: 50%;
					&#btn_reset {
						background-color: var(--color-hitch);
						color: var(--color-hitch-text);
					}
				}
				&.empty-dicepool {
					border-top: 1px solid var(--color-border);
				}
				&.dicepool-presence {
					border-top: 1px solid var(--color-highlight);
					#btn_roll, #btn_set {
						background-color: var(--color-highlight);
						color: var(--color-highlight-text);
					}
				}
			}
		}
	}
	.triptych #dicepool-wrapper {
		width: 100vw;
	}
	#dicepool:not(.empty) .title {
		background-color: var(--color-highlight);
		color: var(--color-highlight-text);
	}
	#dicepool.empty .title {
		background-image: linear-gradient(to top,
			var(--color-background-mute) -100%,
			rgba(0, 0, 0, 0) 50%);
	}
	#dicepool.collapsed .title {
		font-size: x-large;
	}
	#dicepool.expanded .title {
		border-bottom: 1px solid var(--color-border);
		font-size: 1.5em;
	}
</style>

<style>
	/* #dicepool .die {
		height: 5em;
		width: 5em;
	} */
	.landscape {
		#dicepool {
			border-left: 1px solid var(--color-border);
			border-right: 1px solid var(--color-border);
		}
	}
	.dark {
		#dicepool .title {
			text-shadow: none;
		}
		#dicepool.collapsed.empty .title {
			background-color: var(--color-background-mute);
			backdrop-filter: blur(5px);
		}
		#dicepool.expanded .title {
			background-color: var(--color-highlight);
			color: var(--color-highlight-text);
		}
	}
	.light {
		#dicepool {
			#dicepool-limit .button-mnml {
				color: var(--color-highlight-text);
			}
			#dicepool-collapsible {
				background-color: var(--color-background-soft);
			}
		}
		#dicepool.empty .title {
			background-color: var(--color-background-soft);
		}
	}

@keyframes colorChange {
	0% {
		filter: hue-rotate(0deg);
		transform: rotate(0deg);
	}
	100% {
		filter: hue-rotate(360deg);
		transform: rotate(360deg);
	}
}

@keyframes animate {
0% {
transform: rotate(180deg);
}
50% {
transform: rotate(0deg);
}
100% {
transform: rotate(360deg);
}
}

@keyframes animate-reverse {
0% {
transform: rotate(360deg);
}

50% {
transform: rotate(180deg);
}

100% {
transform: rotate(0deg);
}
}
</style>
