<script setup lang="ts">
	import { ref, watch, computed, defineAsyncComponent } from 'vue'
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
	import { die_shapes } from '@/composables/Die'

	import { useDicepoolStore } from '@/stores/DicepoolStore'
	import { usePlayer } from '@/stores/Player'

	import type { Die as DieType } from '@/interfaces/Types'

	const props = defineProps<{
		expanded: boolean
	}>()

	const emit = defineEmits([
		'expand',
		'collapse'
	])

	const player = usePlayer()
	const dicepoolStore = useDicepoolStore()

	const dicepool = useDicepool()

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
			verbose_dice.value = false
			dicepool.pullInterval.value = 3000
			dicepool.pull_dicepools()
		}
		else {
			editing.value = false
			dicepool.pullInterval.value = 10000
		}
	})

	function hide_dicepool() {
		emit('collapse')
	}

	const verbose_dice = ref(true)

	function open_dicepool() {
		emit('expand')
	}

	dicepool.pull_clock()

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
			<div id="dicepool-collapsible" v-if="props.expanded">
				<SessionControl v-if="player.is_gm" />
				<!-- <div id="phase" :class="{ 'pulsate': phase_pulsate }"
					@animationend="phase_pulsate = false">
					{{ editing ? 'change die' : dicepoolStore.phase.toString() }}
				</div> -->
				<div id="dicepools" :style="{ 'background-image': dicepool.dicepool_size.value > 0 ? `url('/img/` + ruleset_logo + `.png')` : '' }">

					<div id="dicepool-picker" v-if="dicepool.inResultPhase.value || dicepool.inEffectPhase.value">

						<span class="info-half result" :class="[{ 'active': dicepool.inResultPhase.value }, { 'pulsate': result_pulsate }]"
								@click.stop="dicepool.set_result_phase()"
								@animationend="result_pulsate = false">
							<div class="header">result{{ ': ' + dicepool.result.value }}</div>
							<div class="info-half-wrapper">
								<input type="button" class="button-mnml" value="-" @click.stop="dicepool.change_result_limit(-1)"
									v-if="dicepool.result_limit.value > 1 && dicepool.inResultPhase.value" />
								<Die v-for="die in dicepoolStore.dice.filter((d) => d.isResultDie && d.ratingType != 'resource')" :key="die.id" :die="die" in_pool
									@click.stop="dicepool.inResultPhase.value ? die.isResultDie = false : dicepool.set_result_phase()" />
								<span class="slot" v-for="i of dicepool.result_limit.value - dicepool.result_size.value" :key="i">
									{{ die_shapes.default_inactive }}
								</span>
								<input type="button" class="button-mnml" value="+" @click.stop="dicepool.change_result_limit(1)"
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
								<Die v-for="die in dicepoolStore.dice.filter((d) => d.isEffectDie)" :die="die" in_pool
										@click.stop="dicepool.inEffectPhase.value ? die.isEffectDie = false : dicepool.set_effect_phase()" />
								<span class="slot" v-for="i of dicepool.effect_limit.value - dicepool.effect_size.value" :key="i">
									{{ die_shapes.default_inactive }}
								</span>
								<input type="button" class="button-mnml" value="+" @click.stop="dicepool.change_effect_limit(1)"
									v-if="dicepool.inEffectPhase.value" />
							</div>
						</span>

					</div>

					<div v-if="dicepool.inSwadeResultPhase.value && dicepoolStore.dice[0].result">
						<div id="swade-result-text">
							<div class="swade-result swade-hitch" v-if="dicepoolStore.dice[0].isHitch">
								<h1>aw shit, a 1!</h1>
								<div class="details">
									<span class="detail">
										result: <Die :die="dicepoolStore.dice[0]" in_pool />
									</span>
									<span class="detail">
										effect: <Die :die="{ number_rating: -2, rating: 'd6' }" />
									</span>
								</div>
							</div>
							<div class="swade-result swade-fail" v-else-if="dicepoolStore.dice[0].result < 4">
								<h1>no bueno, you fail</h1>
								<div class="details">
									<span class="detail">
										result: <Die :die="dicepoolStore.dice[0]" in_pool />
									</span>
									<span class="detail">
										effect: <Die :die="{ number_rating: -1, rating: 'd4' }" />
									</span>
								</div>
							</div>
							<div class="swade-result swade-success" v-else-if="dicepoolStore.dice[0].result < 8">
								<h1>marginal success</h1>
								<div class="details">
									<span class="detail">
										result: <Die :die="dicepoolStore.dice[0]" in_pool />
									</span>
									<span class="detail">
										effect: <Die :die="{ number_rating: 1, rating: 'd4' }" />
									</span>
								</div>
							</div>
							<div class="swade-result swade-raise" v-else-if="dicepoolStore.dice[0].result < 12">
								<h1>great success!</h1>
								<div class="details">
									<span class="detail">
										result: <Die :die="dicepoolStore.dice[0]" in_pool />
									</span>
									<span class="detail">
										effect: <Die :die="{ number_rating: 2, rating: 'd6' }" />
									</span>
								</div>
							</div>
							<div class="swade-result swade-raise" v-else-if="dicepoolStore.dice[0].result < 16">
								<h1>excellent!!</h1>
								<div class="details">
									<span class="detail">
										result: <Die :die="dicepoolStore.dice[0]" in_pool />
									</span>
									<span class="detail">
										effect: <Die :die="{ number_rating: 3, rating: 'd8' }" />
									</span>
								</div>
							</div>
							<div class="swade-result swade-raise" v-else-if="dicepoolStore.dice[0].result < 20">
								<h1>Fucking A!!</h1>
								<div class="details">
									<span class="detail">
										result: <Die :die="dicepoolStore.dice[0]" in_pool />
									</span>
									<span class="detail">
										effect: <Die :die="{ number_rating: 4, rating: 'd10' }" />
									</span>
								</div>
							</div>
							<div class="swade-result swade-raise" v-else>
								<h1>GODLIKE</h1>
								<div class="details">
									<span class="detail">
										result: <Die :die="dicepoolStore.dice[0]" in_pool />
									</span>
									<span class="detail">
										effect: <Die :die="{ number_rating: 5, rating: 'd12' }" />
									</span>
								</div>
							</div>
							<div class="glowing">
								<span style="--i:1;"></span>
								<span style="--i:2;"></span>
								<span style="--i:3;"></span>
							</div>
							
							<div class="glowing">
								<span style="--i:1;"></span>
								<span style="--i:2;"></span>
								<span style="--i:3;"></span>
							</div>
							
							<div class="glowing">
								<span style="--i:1;"></span>
								<span style="--i:2;"></span>
								<span style="--i:3;"></span>
							</div>
							
							<div class="glowing">
								<span style="--i:1;"></span>
								<span style="--i:2;"></span>
								<span style="--i:3;"></span>
							</div>
						</div>
					</div>

					<div id="pool-dice">
						<div id="gm-die-picker" v-if="dicepool.inAddingPhase.value">
							<DiePicker @change-die="add_custom_dice" custom />
						</div>

						<div id="the-meat"
								v-if="!dicepool.inResolvePhase.value">
							<div id="chosen-dice">
								<input type="button" class="button-mnml" id="dicepool-details-view"
									:value="verbose_dice ?
										player.small_buttons ? '👁' : '👁 detail view' :
										player.small_buttons ? '🔘' : '🔘 simple view'"
									@click.stop="verbose_dice = !verbose_dice" />
								<div id="chosen-dice-wrapper">
									<div id="verbose-dice" v-if="verbose_dice">
										<PoolEntity v-for="entity in new Set(dicepoolStore.dice.map(d => d.entityId)).values()" :key="entity"
											:entity_id="entity ?? ''" :dice="dicepoolStore.dice.filter(d => d.entityId == entity)"
											@longpress_die="(die: DieType) => longtap_die(die)" />
									</div>
									<div id="simple-dice" v-else>
										<template v-for="die in dicepool.interactive_dice.value" :key="die.id">
											<DieComponent
												:class="{ 'editing': editing_die && die.id == editing_die.id }"
												:die="die"
												is_choice
												in_pool
												v-touch:hold="()=>longtap_die(die)"
												@click.stop="()=>click_die(die)"
												@click.right="()=>longtap_die(die)"
												@contextmenu.prevent="(e) => e.preventDefault()" />
										</template>
									</div>
								</div>
							</div>
							<div id="edit-die" v-if="editing">
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
	}
	#dicepool-wrapper {
		min-width: 33vw;
		#dicepool-collapsible {
			backdrop-filter: blur(5px);
		}
	}
	.triptych #dicepool-wrapper {
		width: 100vw;
	}
	#dicepool .title {
		font-weight: 500;
		color: var(--color-background);
		border-top: 1px solid var(--color-border);
		cursor: pointer;
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
	#dicepool-collapsible {
		background-color: var(--color-background-mute);
	}
	#dicepools {
		position: relative;
		background-repeat: no-repeat;
		background-position: calc(100% - 20px) calc(100% - 20px);
		background-size: min(200px, 20vw);
		#swade-result-text {
			position: relative;
			overflow: hidden;
			margin: 10px;
			border: 1px solid var(--color-highlight);
			backdrop-filter: blur(5px);
			text-shadow: var(--text-shadow);
			.swade-result {
				display: flex;
				flex-direction: column;
				align-items: center;
				div.details {
					width: 100%;
					display: flex;
					justify-content: space-evenly;
					span.detail {
						display: flex;
						align-items: center;
					}
				}
			}
			/* https://alvarotrigo.com/blog/animated-backgrounds-css/ */
			.glowing {
				position: absolute;
				min-width: 700px;
				height: 550px;
				margin: -150px;
				transform-origin: right;
				animation: colorChange 5s linear infinite;
			}

			.glowing:nth-child(even) {
				transform-origin: left;
			}

			.glowing span {
				position: absolute;
				top: calc(80px * var(--i));
				left: calc(80px * var(--i));
				bottom: calc(80px * var(--i));
				right: calc(80px * var(--i));
			}

			.glowing span::before {
				content: "";
				position: absolute;
				top: 50%;
				left: -8px;
				width: 15px;
				height: 15px;
				background: #f00;
				border-radius: 50%;
			}

			.glowing span:nth-child(3n + 1)::before {
				background: rgba(134,255,0,1);
				box-shadow: 0 0 20px rgba(134,255,0,1),
					0 0 40px rgba(134,255,0,1),
					0 0 60px rgba(134,255,0,1),
					0 0 80px rgba(134,255,0,1),
					0 0 0 8px rgba(134,255,0,.1);
			}

			.glowing span:nth-child(3n + 2)::before {
				background: rgba(255,214,0,1);
				box-shadow: 0 0 20px rgba(255,214,0,1),
					0 0 40px rgba(255,214,0,1),
					0 0 60px rgba(255,214,0,1),
					0 0 80px rgba(255,214,0,1),
					0 0 0 8px rgba(255,214,0,.1);
			}

			.glowing span:nth-child(3n + 3)::before {
				background: rgba(0,226,255,1);
				box-shadow: 0 0 20px rgba(0,226,255,1),
					0 0 40px rgba(0,226,255,1),
					0 0 60px rgba(0,226,255,1),
					0 0 80px rgba(0,226,255,1),
					0 0 0 8px rgba(0,226,255,.1);
			}

			.glowing span:nth-child(3n + 1) {
				animation: animate 10s alternate infinite;
			}

			.glowing span:nth-child(3n + 2) {
				animation: animate-reverse 3s alternate infinite;
			}

			.glowing span:nth-child(3n + 3) {
				animation: animate 8s alternate infinite; 
			}
		}
	}
	#phase {
		text-align: center;
		border-bottom: 1px solid var(--color-border);
	}
	#dicepool-picker {
		display: flex;
		.info-half {
			width: 50%;
			height: 100px;
			border: 1px solid var(--color-border);
			margin: 10px;
			display: flex;
			flex-direction: column;
			justify-content: space-evenly;
			.info-half-wrapper{
				display: flex;
				justify-content: space-evenly;
				align-items: center;
				.slot, .button-mnml {
					font-size: 2em;
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
	#opposing-pools {
		display: flex;
		justify-content: space-around;
		gap: .4em;
	}
	#resolutions {
		/* border-left: 1px solid var(--color-border); */
		padding: .4em;
		display: flex;
		justify-content: center;
		flex-wrap: wrap;
		gap: .4em;
	}
	.edit-die-option {
		text-align: center;
		padding: .2em 0;
	}
	.pickable-die  {
		margin: 0 .2em;
	}
	#resolutions-title {
		font-weight: bold;
		text-align: center;
	}
	#buttons {
		width: 100%;
	}
	.dicepool-button {
		border: none;
		padding: .5em;
		font-size: 1.2em;
		width: 50%;
	}
	#btn_reset {
		background-color: var(--color-hitch);
		color: var(--color-hitch-text);
	}
	.empty-dicepool#buttons {
		border-top: 1px solid var(--color-border);
	}
	.dicepool-presence {
		#buttons {
			border-top: 1px solid var(--color-highlight);
		}
		#btn_roll, #btn_set {
			background-color: var(--color-highlight);
			color: var(--color-highlight-text);
		}
	}
</style>

<style>
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
