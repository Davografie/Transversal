<script setup lang="ts">
import { ref } from 'vue'
import DiePicker from '@/components/DiePicker.vue'
import ScalingEdit from '@/components/ScalingEdit.vue';
import { rating_types } from '@/composables/Rating'
import type { Die as DieType } from '@/interfaces/Types'

const props = defineProps<{
	rating_type: string,
	rating: DieType[],
	pool_scaling: number,
	result_scaling: number,
	effect_scaling: number
}>()

const emit = defineEmits(['change-rating', 'submit', 'cancel'])

const new_rating_type = ref(props.rating_type)
const new_rating = ref(props.rating)
const new_pool_scaling = ref(props.pool_scaling)
const new_result_scaling = ref(props.result_scaling)
const new_effect_scaling = ref(props.effect_scaling)

function increase_rating_type() {
	// cycles through rating types to change trait rating type
	if(new_rating_type.value) {
		new_rating_type.value = rating_types[(rating_types.findIndex(x => x == new_rating_type.value) + 1) % rating_types.length]
	}
	else {
		// sometimes the ratingType is null, so it needs to be created
		new_rating_type.value = rating_types[0]
	}
	emit('change-rating', new_rating_type.value, new_rating.value, new_pool_scaling.value, new_result_scaling.value, new_effect_scaling.value)
}
function decrease_rating_type() {
	// cycles through rating types to change trait rating type
	if(new_rating_type.value) {
		const index = rating_types.findIndex(x => x == new_rating_type.value) - 1;
		new_rating_type.value = rating_types[index < 0 ? rating_types.length - 1 : index];
	}
	else {
		// sometimes the ratingType is null, so it needs to be created
		new_rating_type.value = rating_types[0]
	}
	emit('change-rating', new_rating_type.value, new_rating.value, new_pool_scaling.value, new_result_scaling.value, new_effect_scaling.value)
}
function change_rating_type(rating_type: string) {
	new_rating_type.value = rating_type
	emit('change-rating', new_rating_type.value, new_rating.value, new_pool_scaling.value, new_result_scaling.value, new_effect_scaling.value)
}
function die_picker_change(dice: DieType[]) {
	new_rating.value = dice
	submit()
}
function pool_scaling_change(scaling: number) {
	new_pool_scaling.value = scaling
	submit()
}
function result_scaling_change(scaling: number) {
	new_result_scaling.value = scaling
	submit()
}
function effect_scaling_change(scaling: number) {
	new_effect_scaling.value = scaling
	submit()
}
function submit() {
	emit('change-rating', new_rating_type.value, new_rating.value, new_pool_scaling.value, new_result_scaling.value, new_effect_scaling.value)
}
</script>

<template>
	<div class="rating-edit">
		<div class="scaling">
			<ScalingEdit class="pool-scaling" :scaling="new_pool_scaling" @change-scaling="pool_scaling_change" />
			<ScalingEdit class="result-scaling" :scaling="new_result_scaling" @change-scaling="result_scaling_change" />
			<ScalingEdit class="effect-scaling" :scaling="new_effect_scaling" @change-scaling="effect_scaling_change" />
		</div>
		<div class="rating-types">
			<input type="button" class="button"
				v-for="rating_type in rating_types" :key="rating_type"
				:value="rating_type"
				:class="{ 'active': new_rating_type == rating_type}"
				@click="change_rating_type(rating_type)" />
		</div>
		<DiePicker
			:dice="props.rating"
			preview
			:resource="['resource', 'challenge'].includes(new_rating_type)"
			:negative="new_rating_type == 'challenge'"
			:key="new_rating_type"
			@change-die="die_picker_change"
			@cancel="emit('cancel')"
			v-if="new_rating_type != 'empty'" />
	</div>
</template>

<style scoped>
.rating-edit {
	.rating-types {
		display: flex;
		justify-content: center;
	}
	.scaling {
		display: flex;
		justify-content: center;
		gap: 1em;
		.result-scaling {
			color: var(--color-result-light);
		}
		.effect-scaling {
			color: var(--color-effect);
		}
	}
}
</style>
