<script setup lang="ts">
	import Trait from '@/components/complication/Trait.vue'
	import { useEntity } from '@/composables/Entity'
	import type { Die as DieType } from '@/interfaces/Types'
	
	const props = defineProps<{
		entity_id: string,
		dice: DieType[]
	}>()

	const emits = defineEmits([
		'click_die',
		'click_complication'
	])

	const { entity, retrieve_small_entity } = useEntity(undefined, props.entity_id)
	retrieve_small_entity()
</script>

<template>
	<div class="suggested-entity">
		<div class="entity-name header">
			{{ entity.name }}
		</div>
		<div class="traits">
			<template v-for="traitsetting_id in new Set(props.dice.map((d) => d.traitsettingId)).values()" :key="traitsetting_id">
				<Trait
					:entity_id="props.entity_id"
					:traitsetting_id="traitsetting_id"
					:dice="props.dice.filter((d) => d.traitsettingId == traitsetting_id)"
					@click_die="(die) => emits('click_die', die)"
					@click.stop="emits('click_complication', traitsetting_id)" />
			</template>
		</div>
	</div>
</template>

<style scoped>
</style>
