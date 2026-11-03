/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "GHOST_AndroidVirtualMouse.hh"
#include <cassert>
#include <iostream>
#include <vector>
using namespace ghost::virtual_mouse;
struct Fixture {
  std::vector<Event> events;
  Controller mouse{[this](const Event &e) { events.push_back(e); }};
  uint64_t time = 1000;
  Fixture()
  {
    mouse.set_viewport(1000, 600, 1);
    mouse.sync_cursor(500, 300);
    mouse.set_enabled(true);
    events.clear();
  }
  Point control(int which, int id = 17)
  {
    const Rect &r = mouse.state().controls[which];
    return {id, (r.left + r.right) / 2, (r.top + r.bottom) / 2};
  }
  void down(Point p) { assert(mouse.begin(p.id, p.x, p.y, time)); }
  void up(int id = 17) { mouse.pointer_up(id, time + 100, true); time += 200; }
  void tap(int which) { down(control(which)); up(); }
  int count(Kind kind, int button = 0)
  {
    int n = 0;
    for (auto &e : events) { n += e.kind == kind && (!button || e.button == button); }
    return n;
  }
};
int main()
{
  for (int control : {Left, Middle, Right}) {
    Fixture f;
    f.down(f.control(control));
    assert(f.count(Kind::ButtonDown) == 1 && f.count(Kind::ButtonUp) == 0);
    assert(f.events.back().x == 500 && f.events.back().y == 300);
    assert(f.events.back().button == (1 << (control - Left)));
    f.up();
    assert(f.count(Kind::ButtonUp) == 1 && f.mouse.state().held == 0);
  }
  {
    Fixture f;
    f.down({17, 700, 400}); f.up();
    assert(f.count(Kind::ButtonDown, 1) == 1 && f.count(Kind::ButtonUp, 1) == 1);
    assert(f.mouse.state().x == 500 && f.mouse.state().y == 300);
  }
  {
    Fixture f;
    f.down({17, 700, 400});
    Point p{17, 780, 430}; f.mouse.move(&p, 1); f.up();
    assert(f.mouse.state().x == 580 && f.mouse.state().y == 330);
    assert(f.count(Kind::ButtonDown) == 0);
  }
  for (int control : {Left, Middle, Right}) {
    Fixture f;
    f.tap(Hold);
    assert(f.mouse.state().hold_armed);
    f.tap(control);
    assert(!f.mouse.state().hold_armed && f.mouse.state().held == (1 << (control - Left)));
    assert(f.count(Kind::ButtonDown) == 1 && f.count(Kind::ButtonUp) == 0);
    f.down({17, 750, 400});
    Point p{17, 830, 420}; f.mouse.move(&p, 1); f.up();
    assert(f.mouse.state().x == 580 && f.count(Kind::ButtonDown) == 1);
    f.tap(Hold);
    assert(f.mouse.state().held == 0 && f.count(Kind::ButtonUp) == 1);
  }
  {
    Fixture f;
    f.tap(Hold); f.tap(Right); f.tap(Right);
    assert(f.mouse.state().held == 0 && f.count(Kind::ButtonUp, 4) == 1);
  }
  {
    Fixture f;
    f.down(f.control(Left, 51));
    f.mouse.pointer_down(92, 800, 400, f.time + 10);
    Point points[] = {{92, 870, 420}, f.control(Left, 51)};
    f.mouse.move(points, 2); /* Reordered Android pointer indices must not change ownership. */
    assert(f.mouse.state().x == 570 && f.mouse.state().y == 320);
    f.mouse.pointer_up(51, f.time + 100, false);
    f.mouse.pointer_up(92, f.time + 110, true);
    assert(f.count(Kind::ButtonDown, 1) == 1 && f.count(Kind::ButtonUp, 1) == 1);
  }
  {
    Fixture f;
    f.down({17, 750, 350}); f.mouse.pointer_down(40, 850, 350, f.time);
    Point points[] = {{40, 850, 390}, {17, 750, 390}};
    f.mouse.move(points, 2);
    f.mouse.pointer_up(40, f.time + 100, false); f.up();
    assert(f.count(Kind::Wheel) == 1 && f.events.back().delta == 1);
    assert(f.count(Kind::ButtonDown) == 0 && f.mouse.state().y == 300);
    f.tap(WheelDown); f.tap(WheelUp);
    assert(f.count(Kind::Wheel) == 3 && f.events.back().delta == 1);
  }
  {
    Fixture f;
    f.tap(Hold); f.tap(Left); f.mouse.cancel();
    assert(f.mouse.state().held == 0 && f.count(Kind::ButtonUp) == 1);
    f.down(f.control(Right));
    f.mouse.set_viewport(600, 1000, 1);
    assert(f.mouse.state().held == 0 && f.mouse.capturing());
    f.up(); assert(!f.mouse.capturing());
  }
  {
    Fixture f;
    f.tap(Hold); f.tap(Middle); f.down(f.control(Close));
    assert(!f.mouse.state().enabled && f.mouse.capturing());
    assert(f.mouse.state().held == 0 && f.count(Kind::ButtonUp, 2) == 1);
    f.up();
    assert(!f.mouse.capturing() && f.count(Kind::ButtonDown, 1) == 0);
    assert(!f.mouse.begin(17, 700, 300, f.time));
  }
  {
    Fixture f;
    Rect keyboard{0, 0, 1000, 400};
    f.mouse.set_keyboard_rect(keyboard);
    assert(!f.mouse.state().panel.intersects(keyboard));
    assert(!f.mouse.begin(17, 200, 300, f.time));
    assert(!f.mouse.capturing() && f.events.empty());
    assert(f.mouse.begin(17, 900, 550, f.time)); f.up();
  }
  {
    Fixture f;
    Point grip = f.control(Move);
    f.down(grip); grip.x += 50; grip.y += 100; f.mouse.move(&grip, 1); f.up();
    assert(f.mouse.state().panel.top == 138);
    assert(f.mouse.state().x == 500 && f.mouse.state().y == 300 && f.events.empty());
  }
  {
    Fixture f;
    f.down({17, 700, 400}); f.mouse.cancel(true);
    Point p{17, 900, 500}; f.mouse.move(&p, 1); f.up();
    assert(f.events.empty()); /* Focus/surface loss discards the remainder without click-through. */
    f.mouse.sync_cursor(9999, -200); assert(f.mouse.state().x == 999 && f.mouse.state().y == 0);
  }
  std::cout << "Virtual mouse: clicks, relative motion, latch, multitouch, scrolling, keyboard, lifecycle passed\n";
}
