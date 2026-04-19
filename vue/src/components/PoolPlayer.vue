<script setup lang="ts">
	import { ref, computed } from 'vue'
	import { useDicepoolStore } from '@/stores/DicepoolStore'
	import { usePlayerStore } from '@/stores/PlayerStore'
	import { die_shapes } from '@/composables/Die'
	import { WsDicepool } from '@/interfaces/WebsocketTypes'
	import Die from '@/components/Die.vue'
	import PoolEntity from '@/components/PoolEntity.vue'
	import Resolution from '@/components/Resolution.vue'
	const props = defineProps<{
		dicepool: WsDicepool,
	}>()
	const player = usePlayerStore()

	const dicepoolStore = useDicepoolStore()
	const verbose_dice = ref(false)
	const result_limit = computed(() => {
		let mod = 0
		const unique_traits = [...new Set(props.dicepool.dice.map(d => d.traitsettingId))]
		unique_traits.forEach(t => {
			const trait_dice = props.dicepool.dice.filter(d => d.traitsettingId == t)
			if(trait_dice.length > 0 && trait_dice[0].resultScaling) {
				mod += trait_dice[0].resultScaling
			}
		})
		return dicepoolStore.base_result_limit + mod
	})
	const effect_limit = computed(() => {
		let mod = 0
		const unique_traits = [...new Set(props.dicepool.dice.map(d => d.traitsettingId))]
		unique_traits.forEach(t => {
			const trait_dice = props.dicepool.dice.filter(d => d.traitsettingId == t)
			if(trait_dice.length > 0 && trait_dice[0].effectScaling) {
				mod += trait_dice[0].effectScaling
			}
		})
		return dicepoolStore.effect_limit + mod
	})
	const remaining_dice = computed(() => {
		return props.dicepool.dice.length - result_limit.value - effect_limit.value
	})
</script>

<template>
	<div class="pool-player" :class="{ 'active': dicepool.player.key == player.player.key }" @click.stop="verbose_dice = !verbose_dice">
		<div class="player">
			<!-- <div>
				{{ verbose_dice ?
					player.small_buttons ? '👁' : '👁 detail view' :
					player.small_buttons ? '🔘' : '🔘 simple view' }}
			</div> -->
			<div class="name">
				<span class="header">
					{{ dicepool.player.name }}
				</span>
				<span class="phase">
					{{ dicepool.phase }}
				</span>
			</div>
			<div class="limiters">
				<span class="dicepool-size">
					<span class="empty-die" v-if="remaining_dice > 0" v-for="i in remaining_dice" :key="i">
						{{ die_shapes.default_active }}
					</span>
				</span>
				<span class="result-limit">
					<span class="empty-die" v-for="i in result_limit" :key="i">
						{{ die_shapes.default_active }}
					</span>
				</span>
				<span class="effect-limit">
					<span class="empty-die" v-for="i in effect_limit" :key="i">
						{{ die_shapes.default_active }}
					</span>
				</span>
			</div>
		</div>
		<div class="active-pool" v-if="dicepool.player.phase != dicepoolStore.phases.RESOLVE">
			<div class="dice" v-if="!verbose_dice">
				<Die v-for="d in dicepool.dice" :key="d.id" :die="d" in_pool />
			</div>
			<div class="verbose-dice" v-if="verbose_dice">
				<PoolEntity
					v-for="entity in new Set(props.dicepool.dice.map(d => d.entityId)).values()" :key="entity"
					:entity_id="entity ?? ''"
					:dice="props.dicepool.dice.filter(d => d.entityId == entity)" />
				<!-- <PoolEntity
					v-for="entity in new Set(dicepool.dice.map((d) => d.entityId))"
					:key="entity"
					:dice="dicepool.dice.filter((d) => d.entityId == entity)"
					:entity_id="entity" /> -->
			</div>
		</div>
		<div class="resolved-pool" v-if="dicepool.player.phase == dicepoolStore.phases.RESOLVE">
			<Resolution :resolution="dicepool" :winner="dicepool.winner ?? false" :heroic="dicepool.heroic" :verbose="verbose_dice" />
		</div>
	</div>
</template>

<style scoped>
.pool-player {
	padding: .4em 1em;
	border: 1px solid var(--color-border);
	border-radius: 1em;
	background-color: var(--color-background);
	&.active {
		border: 1px solid var(--color-highlight);
	}
	.player {
		text-align: center;
		.limiters {
			font-size: 2em;
			.result-limit {
				color: var(--color-result);
			}
			.effect-limit {
				color: var(--color-effect);
			}
		}
	}
}
</style>

<style>
.dark .pool-player {
	&.active {
		box-shadow: inset 0 0 30px var(--color-highlight-mute);
	}
}
</style>
