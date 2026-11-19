import { Component, type ReactNode } from "react";

/** Keeps an error in one widget (e.g. the chat) from blanking the whole page: only the widget disappears. */
export default class SafeWidget extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: unknown) {
    console.error("Widget error:", error);
  }

  render() {
    return this.state.failed ? null : this.props.children;
  }
}
