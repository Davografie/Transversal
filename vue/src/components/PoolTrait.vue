<script setup lang="ts">
	import { ref, computed } from 'vue'
	import Die from '@/components/Die.vue'
	import PoolTrait from '@/components/PoolTrait.vue'
	import { useTrait } from '@/composables/Trait'
	import { useSFX } from '@/composables/SFX'
	import { useDicepool } from '@/composables/Dicepool'
	import type { Die as DieType } from '@/interfaces/Types'
	import DiePicker from '@/components/DiePicker.vue'
	
	const props = defineProps<{
		traitsetting_id: string
		dice: DieType[]
	}>()

	const emit = defineEmits(['longpress_die'])
	
	const dicepool = useDicepool(false)
	const { trait, retrieve_trait } = useTrait(undefined, undefined, props.traitsetting_id, props.dice[0]?.entityId)
	const { sfx, retrieve_sfx } = useSFX(undefined, props.dice[0]?.sfxId)

	retrieve_trait()
	retrieve_sfx()

	// used to discern between click and longpress
	const held = ref(false)

	function click_die(die: DieType) {
		if(!held.value) {
			if(dicepool.inAddingPhase.value) dicepool.remove_die(die)
			else if(dicepool.inResultPhase.value) {
				die.isResultDie = !die.isResultDie
				if(dicepool.result_size.value == dicepool.result_limit.value) dicepool.next()
			}
			else if(dicepool.inEffectPhase.value && !die.isResultDie) {
				die.isEffectDie = !die.isEffectDie
			}
		}
	}

	function longpress_die(die: DieType) {
		held.value = true
		// emit('longpress_die', die)
		edit_die.value = die
		editing_dice.value = true
		setTimeout(() => {
			held.value = false
		}, 500)
	}

	const trait_class = computed(() => {
		if(dicepool.inEffectPhase.value && props.dice.some((d) => !d.isResultDie)) return 'available'
		if(dicepool.inEffectPhase.value && props.dice.every((d) => d.isResultDie)) return 'unavailable'
	})
	
	const editing_dice = ref(false)
	const edit_die = ref<DieType>()

	async function change_die(rating: DieType[]) {
		if(edit_die.value) await dicepool.remove_die(edit_die.value)
		dicepool.add_dice(rating)
		editing_dice.value = false
		edit_die.value = undefined
	}
</script>

<template>
	<div class="pool-wrapper"
			:class="trait_class">
		<div class="pool-trait-wrapper">
			<div class="pool-trait-description">
				<div class="trait-name" v-if="!trait.statement">
					{{ trait.name }}
				</div>
				<div class="trait-statement" v-if="trait.statement">
					{{ trait.statement ? trait.statement : '' }}
				</div>
				<div class="trait-sfx" v-if="sfx && sfx.id != 'placeholder'">
					✨ {{ sfx.name }}
				</div>
			</div>
			<div class="pool-trait-rating">
				<Die class="pool-die" v-for="die in props.dice.filter((d) => (d.traitsettingId == props.traitsetting_id && !d.subTraitsettingId) || 
					(d.subTraitsettingId && d.subTraitsettingId == props.traitsetting_id))"
					:die="die"
					in_pool
					is_choice
					size="2em"
					v-touch:hold="() => longpress_die(die)"
					@click.right="() => longpress_die(die)"
					@click.stop="click_die(die)" />
			</div>
		</div>
		<DiePicker
			v-if="editing_dice"
			show_effects
			:die="edit_die"
			@change-die="(rating) => change_die(rating)" />
		<div class="subtraits" v-if="trait.subTraits && trait.subTraits?.length > 0">
			<template v-for="subtrait in trait.subTraits" :key="subtrait.id">
				<PoolTrait v-if="props.dice.filter((d) => d.subTraitsettingId == subtrait.traitSettingId).length > 0"
					:traitsetting_id="subtrait.traitSettingId ?? ''"
					:dice="props.dice.filter((d) => d.subTraitsettingId == subtrait.traitSettingId)" />
			</template>
		</div>
	</div>
</template>

<style scoped>
	.pool-trait-wrapper {
		/* border-bottom: 1px solid var(--color-border); */
		display: flex;
		justify-content: space-between;
		align-items: center;
		position: relative;
		max-height: 1.6em;
		&:hover {
			box-shadow: inset 0 0 10px var(--color-highlight);
			cursor: crosshair;
		}
		&.unavailable {
			color: var(--color-disabled);
		}
		.subtraits {
			/* display: flex;
			flex-direction: column; */
			/* line-height: 0.2em; */
		}
		.pool-trait-rating {
			/* float: right; */
			/* position: absolute;
			right: 0; */
			transform: translateY(-.4em);
		}
	}
	.pool-wrapper {
		padding-left: 1em;
		.pool-trait-description {
			display: flex;
			flex-direction: column;
			justify-content: center;
			.trait-name {
				font-weight: bold;
			}
			.trait-statement {
				font-size: 1.2em;
			}
			.trait-sfx {
				font-style: italic;
			}
		}
	}
</style>
