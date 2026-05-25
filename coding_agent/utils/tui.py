"""Interactive TUI components for the coding agent CLI."""

import sys
from typing import Optional, Callable


class PlanSelector:
    """Interactive plan selector using keyboard navigation.
    
    Allows users to navigate through plan items and toggle their enabled status
    using arrow keys and space bar.
    """
    
    def __init__(self, plan_items: list) -> None:
        """Initialize the plan selector.
        
        Args:
            plan_items: List of plan items (dicts with 'description', 'enabled' keys).
        """
        self.items = plan_items
        self.selected_index = 0
    
    def render(self) -> str:
        """Render the current state of the plan selector.
        
        Returns:
            String representation of the plan selector UI.
        """
        lines = []
        lines.append("Select plan items to execute (↑↓ to navigate, Space to toggle, Enter to confirm):")
        lines.append("")
        
        for i, item in enumerate(self.items):
            prefix = "► " if i == self.selected_index else "  "
            status = "☑" if item.get('enabled', False) else "☐"
            description = item.get('description', 'Unknown')
            tool_info = f" [tool: {item.get('tool_name', 'none')}]" if item.get('tool_name') else ""
            lines.append(f"{prefix}{status} {i + 1}. {description}{tool_info}")
        
        lines.append("")
        lines.append("Controls:")
        lines.append("  ↑/↓ or k/j : Navigate between items")
        lines.append("  Space      : Toggle selected item")
        lines.append("  a          : Select all items")
        lines.append("  n          : Deselect all items")
        lines.append("  Enter      : Confirm selection")
        lines.append("  q          : Cancel")
        
        return "\n".join(lines)
    
    def move_selection(self, delta: int) -> None:
        """Move the selection up or down.
        
        Args:
            delta: Number of positions to move (positive for down, negative for up).
        """
        self.selected_index = max(0, min(len(self.items) - 1, self.selected_index + delta))
    
    def toggle_selected(self) -> bool:
        """Toggle the enabled status of the selected item.
        
        Returns:
            New enabled status of the selected item.
        """
        if not self.items:
            return False
        
        current = self.items[self.selected_index].get('enabled', False)
        self.items[self.selected_index]['enabled'] = not current
        return not current
    
    def select_all(self) -> None:
        """Select all items."""
        for item in self.items:
            item['enabled'] = True
    
    def deselect_all(self) -> None:
        """Deselect all items."""
        for item in self.items:
            item['enabled'] = False
    
    def get_enabled_items(self) -> list:
        """Get only enabled items.
        
        Returns:
            List of enabled plan items.
        """
        return [item for item in self.items if item.get('enabled', False)]


def simple_plan_selector(plan_items: list) -> tuple[bool, list]:
    """Simple text-based plan selector without TUI dependencies.
    
    This is a fallback for environments without curses support.
    
    Args:
        plan_items: List of plan items (dicts with 'description', 'enabled' keys).
    
    Returns:
        Tuple of (confirmed, enabled_items) where confirmed is whether user approved.
    """
    print("\n" + "=" * 70)
    print("PLAN REVIEW")
    print("=" * 70)
    
    # Display items with numbers
    for i, item in enumerate(plan_items, 1):
        status = "✓" if item.get('enabled', False) else "✗"
        description = item.get('description', 'Unknown')
        tool_info = f" [tool: {item.get('tool_name', 'none')}]" if item.get('tool_name') else ""
        print(f"  {i}. [{status}] {description}{tool_info}")
    
    print("\n" + "-" * 70)
    print("Commands:")
    print("  <number>     : Toggle item (e.g., type '1' to toggle first item)")
    print("  a            : Select all items")
    print("  n            : Deselect all items")
    print("  y / Enter    : Confirm and proceed")
    print("  q            : Cancel")
    print("-" * 70)
    
    while True:
        try:
            user_input = input("\nYour choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return False, []
        
        if not user_input:
            continue
        
        if user_input in ('y', 'yes'):
            enabled = [item for item in plan_items if item.get('enabled', False)]
            print(f"\nConfirmed! Will execute {len(enabled)} of {len(plan_items)} items.")
            return True, enabled
        
        if user_input in ('q', 'quit', 'cancel'):
            print("\nCancelled.")
            return False, []
        
        if user_input == 'a':
            for item in plan_items:
                item['enabled'] = True
            print("\nAll items selected.")
            # Re-display
            for i, item in enumerate(plan_items, 1):
                status = "✓" if item.get('enabled', False) else "✗"
                description = item.get('description', 'Unknown')
                tool_info = f" [tool: {item.get('tool_name', 'none')}]" if item.get('tool_name') else ""
                print(f"  {i}. [{status}] {description}{tool_info}")
            continue
        
        if user_input == 'n':
            for item in plan_items:
                item['enabled'] = False
            print("\nAll items deselected.")
            # Re-display
            for i, item in enumerate(plan_items, 1):
                status = "✓" if item.get('enabled', False) else "✗"
                description = item.get('description', 'Unknown')
                tool_info = f" [tool: {item.get('tool_name', 'none')}]" if item.get('tool_name') else ""
                print(f"  {i}. [{status}] {description}{tool_info}")
            continue
        
        # Try to parse as number
        try:
            num = int(user_input)
            if 1 <= num <= len(plan_items):
                idx = num - 1
                plan_items[idx]['enabled'] = not plan_items[idx].get('enabled', False)
                status = "✓" if plan_items[idx]['enabled'] else "✗"
                print(f"\nToggled item {num}: {plan_items[idx]['description']} [{status}]")
                
                # Re-display
                for i, item in enumerate(plan_items, 1):
                    status = "✓" if item.get('enabled', False) else "✗"
                    description = item.get('description', 'Unknown')
                    tool_info = f" [tool: {item.get('tool_name', 'none')}]" if item.get('tool_name') else ""
                    print(f"  {i}. [{status}] {description}{tool_info}")
                continue
            else:
                print(f"Please enter a number between 1 and {len(plan_items)}")
        except ValueError:
            print(f"Unknown command: {user_input}. Type 'y' to confirm or 'q' to cancel.")
    
    return False, []


try:
    import curses
    
    def curses_plan_selector(plan_items: list) -> tuple[bool, list]:
        """Curses-based interactive plan selector.
        
        Args:
            plan_items: List of plan items (dicts with 'description', 'enabled' keys).
        
        Returns:
            Tuple of (confirmed, enabled_items) where confirmed is whether user approved.
        """
        result = {'confirmed': False, 'items': plan_items}
        
        def main(stdscr):
            # Setup curses
            curses.curs_set(0)  # Hide cursor
            stdscr.keypad(True)
            
            selected_idx = 0
            
            while True:
                stdscr.clear()
                height, width = stdscr.getmaxyx()
                
                # Title
                title = " PLAN SELECTION (↑↓ navigate, Space toggle, Enter confirm) "
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(0, 0, title.center(width - 1)[:width - 1])
                stdscr.attroff(curses.A_REVERSE)
                
                # Items
                for i, item in enumerate(plan_items):
                    if i >= height - 4:
                        break
                    
                    prefix = ">" if i == selected_idx else " "
                    status = "[X]" if item.get('enabled', False) else "[ ]"
                    description = item.get('description', 'Unknown')[:width - 20]
                    tool_info = f" ({item.get('tool_name', '')})" if item.get('tool_name') else ""
                    
                    line = f"{prefix}{status} {i + 1}. {description}{tool_info}"
                    stdscr.addstr(i + 2, 2, line[:width - 3])
                
                # Instructions
                instructions = "Space: Toggle | ↑↓: Navigate | a: All | n: None | Enter: OK | q: Quit"
                stdscr.addstr(height - 2, 2, instructions[:width - 3])
                
                stdscr.refresh()
                
                # Handle input
                key = stdscr.getch()
                
                if key == ord('q') or key == ord('Q'):
                    result['confirmed'] = False
                    return
                
                if key == curses.KEY_UP or key == ord('k') or key == ord('j') and False:
                    selected_idx = max(0, selected_idx - 1)
                
                elif key == curses.KEY_DOWN or key == ord('j'):
                    selected_idx = min(len(plan_items) - 1, selected_idx + 1)
                
                elif key == ord(' '):
                    if plan_items:
                        current = plan_items[selected_idx].get('enabled', False)
                        plan_items[selected_idx]['enabled'] = not current
                
                elif key == ord('a') or key == ord('A'):
                    for item in plan_items:
                        item['enabled'] = True
                
                elif key == ord('n') or key == ord('N'):
                    for item in plan_items:
                        item['enabled'] = False
                
                elif key == curses.KEY_ENTER or key == 10 or key == 13:
                    result['confirmed'] = True
                    result['items'] = [item for item in plan_items if item.get('enabled', False)]
                    return
        
        curses.wrapper(main)
        return result['confirmed'], result['items']
    
    HAS_CURSES = True

except ImportError:
    HAS_CURSES = False
    curses_plan_selector = None  # type: ignore


def interactive_plan_selector(plan_items: list, use_curses: bool = True) -> tuple[bool, list]:
    """Choose the best available plan selector for the environment.
    
    Args:
        plan_items: List of plan items (dicts with 'description', 'enabled' keys).
        use_curses: Whether to try using curses if available.
    
    Returns:
        Tuple of (confirmed, enabled_items) where confirmed is whether user approved.
    """
    if use_curses and HAS_CURSES and sys.stdout.isatty():
        try:
            return curses_plan_selector(plan_items)
        except Exception:
            pass
    
    return simple_plan_selector(plan_items)
