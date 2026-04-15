<script setup lang="ts">
	import { onUnmounted } from 'vue'

	import { usePlayerStore } from '@/stores/PlayerStore'
	import { useDicepoolWS } from '@/composables/DicepoolWS'
	
	const player = usePlayerStore()
	const websocket = useDicepoolWS()

	onUnmounted(() => {
		console.log("closing websocket")
		websocket.close()
	})

	function engage() {
		websocket.engage()
	}

	defineExpose({
		engage,
	})
</script>

<template>
	<div id="websocket-connection" v-if="player.is_gm">
		<span v-if="websocket.receiving.value" title="receiving">⚫</span>
		<span v-else-if="websocket.status.value == 'OPEN'" :title="websocket.status.value">🟢</span>
		<span v-else-if="websocket.status.value == 'CONNECTING'" :title="websocket.status.value">🟡</span>
		<span v-else :title="websocket.status.value">🔴</span>
	</div>
</template>

<style scoped>
</style>
