<script setup lang="ts"></script>

<template>
    <div class="resource" v-for="ratings, resource in traits">
        <div class="label">{{ resource }}</div>
        <div class="resource-die" :class="ratings.d4 > 0 ? 'rd4' : 'dis-rd'">
            <div class="amount">{{ ratings.d4 }}</div>
            <div class="die" :class="ratings.d4 > 0 ? 'd4' : 'dis-die'">d4</div>
        </div>
        <div class="resource-die" :class="ratings.d6 > 0 ? 'rd6' : 'dis-rd'">
            <div class="amount">{{ ratings.d6 }}</div>
            <div class="die" :class="ratings.d6 > 0 ? 'd6' : 'dis-die'">d6</div>
        </div>
        <div class="resource-die" :class="ratings.d8 > 0 ? 'rd8' : 'dis-rd'">
            <div class="amount">{{ ratings.d8 }}</div>
            <div class="die" :class="ratings.d8 > 0 ? 'd8' : 'dis-die'">d8</div>
        </div>
        <div class="resource-die" :class="ratings.d10 > 0 ? 'rd10' : 'dis-rd'">
            <div class="amount">{{ ratings.d10 }}</div>
            <div class="die" :class="ratings.d10 > 0 ? 'd10' : 'dis-die'">d10</div>
        </div>
        <div class="resource-die" :class="ratings.d12 > 0 ? 'rd12' : 'dis-rd'">
            <div class="amount">{{ ratings.d12 }}</div>
            <div class="die" :class="ratings.d12 > 0 ? 'd12' : 'dis-die'">d12</div>
        </div>
    </div>
</template>

<style scoped>
.resource-die {
	display: inline-block;
	border-radius: 25px;
	margin: 0 4px;
}
.rd4 {
	border: 2px solid var(--color-die-4);
}
.rd6 {
	border: 2px solid var(--color-die-6);
}
.rd8 {
	border: 2px solid var(--color-die-8);
}
.rd10 {
	border: 2px solid var(--color-die-10);
}
.rd12 {
	border: 2px solid var(--color-die-12);
}
.dis-rd {
	border: 2px solid var(--color-text);
}
.resource-die .amount {
	display: inline-block;
	padding: 0 8px;
}
</style>
