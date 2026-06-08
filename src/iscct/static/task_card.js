export const TaskCard = {
  props: ['task', 'expanded', 'badgeClass', 'toggleTask', 'formatDuration'],
  template: `
    <article class="task-card" :class="{ open: expanded }">
      <button class="task-head" @click="toggleTask(task.task_id)">
        <span class="task-id">{{ task.task_id }}</span>
        <span class="task-title">{{ task.title }}</span>
        <span class="task-owner">{{ task.assignee }}</span>
        <span class="task-time">{{ formatDuration(task.started_at) }}</span>
        <span class="status" :class="badgeClass(task.status)">{{ task.status }}</span>
        <span class="chev">▾</span>
      </button>

      <div class="task-body" v-if="expanded">
        <div class="steps">
          <div class="step" v-for="step in task.steps" :key="step.name">
            <div class="step-icon" :class="step.stateClass">{{ step.icon }}</div>
            <div>
              <div class="step-name">{{ step.name }}</div>
              <div class="step-meta">{{ step.meta }}</div>
              <div class="step-note" v-if="step.note">{{ step.note }}</div>
            </div>
          </div>
        </div>
      </div>
    </article>
  `,
};
