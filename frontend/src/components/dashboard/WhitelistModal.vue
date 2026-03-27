<script setup lang="ts">
import type { Whitelist } from "../../api";
import { copy } from "../../constants/copy";
import UiButton from "../ui/UiButton.vue";
import UiModal from "../ui/UiModal.vue";

defineProps<{
    open: boolean;
    roomTitle: string;
    lists: Whitelist[];
    loading: boolean;
    editingId: number | null;
    errorMessage: string;
}>();

const newName = defineModel<string>("newName", { required: true });
const newUrls = defineModel<string>("newUrls", { required: true });
const showForm = defineModel<boolean>("showForm", { required: true });
const editName = defineModel<string>("editName", { required: true });
const editUrls = defineModel<string>("editUrls", { required: true });

const emit = defineEmits<{
    close: [];
    toggleForm: [];
    create: [];
    saveWhitelist: [];
    cancelEdit: [];
    delete: [id: number];
    edit: [item: Whitelist];
}>();
</script>

<template>
    <UiModal :open="open" @close="emit('close')">
        <header class="modal-header">
            <div>
                <p class="modal-eyebrow">{{ copy.dashboard.modalEyebrow }}</p>
                <h3>{{ roomTitle }}</h3>
            </div>
            <UiButton variant="ghost" type="button" @click="emit('close')">
                {{ copy.dashboard.modalClose }}
            </UiButton>
        </header>

        <div class="modal-toolbar">
            <UiButton
                variant="primary"
                type="button"
                @click="emit('toggleForm')"
            >
                {{
                    showForm
                        ? copy.dashboard.hideForm
                        : copy.dashboard.newWhitelist
                }}
            </UiButton>
        </div>

        <p v-if="errorMessage" class="error-alert">{{ errorMessage }}</p>

        <div v-if="showForm" class="editor-box">
            <input
                v-model="newName"
                type="text"
                class="field"
                :placeholder="copy.dashboard.newNamePlaceholder"
            />
            <textarea
                v-model="newUrls"
                rows="5"
                class="field field-area"
                :placeholder="copy.dashboard.newUrlsPlaceholder"
            />
            <UiButton
                variant="primary"
                type="button"
                :disabled="loading"
                @click="emit('create')"
            >
                {{ copy.dashboard.create }}
            </UiButton>
        </div>

        <p v-if="lists.length === 0 && !showForm" class="empty">
            {{ copy.dashboard.emptyWhitelists }}
        </p>

        <div class="whitelist-list">
            <article v-for="wl in lists" :key="wl.id" class="whitelist-card">
                <div
                    v-if="editingId === wl.id"
                    class="editor-box editor-inline"
                >
                    <input
                        v-model="editName"
                        type="text"
                        class="field"
                        :placeholder="copy.dashboard.editNamePlaceholder"
                    />
                    <textarea
                        v-model="editUrls"
                        rows="5"
                        class="field field-area"
                        :placeholder="copy.dashboard.editUrlsPlaceholder"
                    />
                    <div class="inline-actions">
                        <UiButton
                            variant="primary"
                            type="button"
                            :disabled="loading"
                            @click.stop="emit('saveWhitelist')"
                        >
                            {{ copy.dashboard.save }}
                        </UiButton>
                        <UiButton
                            variant="light"
                            type="button"
                            :disabled="loading"
                            @click.stop="emit('cancelEdit')"
                        >
                            {{ copy.dashboard.cancel }}
                        </UiButton>
                    </div>
                </div>

                <div v-else>
                    <header class="whitelist-head">
                        <h4>{{ wl.name }}</h4>
                        <div class="inline-actions">
                            <UiButton
                                variant="icon"
                                type="button"
                                @click.stop="emit('edit', wl)"
                            >
                                {{ copy.dashboard.edit }}
                            </UiButton>
                            <UiButton
                                variant="iconDanger"
                                type="button"
                                @click.stop="emit('delete', wl.id)"
                            >
                                {{ copy.dashboard.delete }}
                            </UiButton>
                        </div>
                    </header>

                    <ul class="url-list">
                        <li v-for="(url, idx) in wl.urls" :key="idx">
                            {{ url }}
                        </li>
                    </ul>
                </div>
            </article>
        </div>
    </UiModal>
</template>

<style scoped>
.modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 0.8rem;
}

.modal-header h3 {
    margin: 0;
    font-size: 1.1rem;
}

.modal-eyebrow {
    margin: 0;
    color: var(--color-muted);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.modal-toolbar {
    margin-bottom: 0.8rem;
}

.editor-box {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    background: var(--color-surface-muted);
    padding: 0.8rem;
    margin-bottom: 0.8rem;
}

.field {
    width: 100%;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-surface);
    padding: 0.62rem 0.7rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}

.field-area {
    min-height: 120px;
    resize: vertical;
    font-family: var(--font-mono);
}

.empty {
    border: 1px dashed var(--color-border);
    border-radius: var(--radius-lg);
    padding: 0.8rem;
    color: var(--color-muted);
}

.error-alert {
    margin: 0 0 0.8rem;
    border: 1px solid var(--color-error-border);
    border-radius: var(--radius-md);
    background: var(--color-error-bg);
    padding: 0.7rem 0.8rem;
    color: var(--color-error-text);
}

.whitelist-list {
    display: grid;
    gap: 0.7rem;
}

.whitelist-card {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    background: var(--color-surface);
    padding: 0.75rem;
}

.whitelist-head {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    align-items: flex-start;
    margin-bottom: 0.45rem;
}

.whitelist-head h4 {
    margin: 0;
    font-size: 0.98rem;
}

.inline-actions {
    display: flex;
    gap: 0.45rem;
}

.url-list {
    margin: 0;
    padding-left: 1rem;
    color: var(--color-muted);
    font-size: 0.86rem;
}

.url-list li {
    margin-bottom: 0.2rem;
    font-family: var(--font-mono);
    word-break: break-all;
}

.editor-inline {
    margin-bottom: 0;
}
</style>
