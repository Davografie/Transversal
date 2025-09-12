<script setup lang="ts">
import { ref } from 'vue'
import DiePicker from '@/components/DiePicker.vue'
import { rating_types } from '@/composables/Rating'
import type { Die as DieType } from '@/interfaces/Types'

const props = defineProps<{
	rating_type: string,
	rating: DieType[]
}>()

const emit = defineEmits(['change-rating', 'submit', 'cancel'])

const new_rating_type = ref(props.rating_type)
const new_rating = ref(props.rating)

function increase_rating_type() {
	// cycles through rating types to change trait rating type
	if(new_rating_type.value) {
		new_rating_type.value = rating_types[(rating_types.findIndex(x => x == new_rating_type.value) + 1) % rating_types.length]
	}
	else {
		// sometimes the ratingType is null, so it needs to be created
		new_rating_type.value = rating_types[0]
	}
	emit('change-rating', new_rating_type.value, new_rating.value)
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
	emit('change-rating', new_rating_type.value, new_rating.value)
}
function die_picker_change(dice: DieType[]) {
	new_rating.value = dice
	submit()
}
function submit() {
	emit('change-rating', new_rating_type.value, new_rating.value)
}
</script>

<template>
	<div>
		<input type="button" class="button"
			:value="new_rating_type"
			@click.stop="increase_rating_type"
			@click.right="decrease_rating_type" />
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
</style>
