<script setup lang="ts">
	import { useRelation } from '@/composables/Relation'
	import { RouterLink } from 'vue-router'
	const props = defineProps<{
		relation_id: string
	}>()
	const { relation, retrieve_relation } = useRelation(undefined, props.relation_id)
	retrieve_relation()
</script>

<template>
	<div class="resolution-relation-wrapper">
		<RouterLink :to="'/entity/' + relation.toEntity.key" v-if="relation.toEntity">
			{{ relation.toEntity.name }}
		</RouterLink>
	</div>
</template>

<style scoped>
</style>
