export const ChatBubble = {
  props: ['message'],
  template: `
    <div class="bubble-row" :class="message.role">
      <div class="bubble-label">{{ message.author }} · {{ message.time }}</div>
      <div class="bubble" :class="message.role" v-html="message.html"></div>
    </div>
  `,
};
