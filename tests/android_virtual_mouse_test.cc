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
    assert(f.count(Kind::ButtonDown) == 0);
    f.mouse.tick(f.time + 240);
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
    f.mouse.pointer_down(99, 950, 350, f.time);
    Point points[] = {{99, 950, 390}, {40, 850, 390}, {17, 750, 390}};
    f.mouse.move(points, 3);
    f.mouse.pointer_up(99, f.time + 90, false);
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
    assert(!keyboard.contains(f.mouse.state().x, f.mouse.state().y));
    f.events.clear();
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
  {
    Fixture f;
    f.mouse.set_keyboard_rect({0, 400, 1000, 600});
    f.tap(Hold); f.tap(Left);
    f.down({17, 800, 300});
    Point p{17, 800, 500}; f.mouse.move(&p, 1); f.up();
    assert(f.mouse.state().y == 399 && f.mouse.state().held == 1);
    f.tap(Hold);
    assert(f.count(Kind::ButtonUp, 1) == 1 && f.events.back().y == 399);
  }
  {
    Fixture f;
    f.down({17, 750, 350}); f.up();
    f.mouse.tick(1339); assert(f.count(Kind::ButtonDown) == 0);
    f.mouse.tick(1340); assert(f.count(Kind::ButtonDown, 1) == 1);
    f.mouse.tick(2000); assert(f.count(Kind::ButtonDown) == 1);
  }
  {
    Fixture f;
    f.down({17, 750, 350}); f.up();
    f.down({17, 750, 350}); f.up();
    f.mouse.tick(3000);
    assert(f.count(Kind::ButtonDown, 1) == 0 && f.count(Kind::ButtonDown, 4) == 1);
    assert(f.count(Kind::ButtonUp, 4) == 1);
  }
  {
    Fixture f;
    f.down({17, 750, 350}); f.up();
    f.down({17, 900, 350}); f.up();
    f.mouse.tick(3000);
    assert(f.count(Kind::ButtonDown, 1) == 2 && f.count(Kind::ButtonDown, 4) == 0);
  }
  {
    Fixture f;
    f.down({17, 750, 350}); f.up();
    f.down({17, 750, 350});
    Point p{17, 810, 350}; f.mouse.move(&p, 1); f.up(); f.mouse.tick(3000);
    assert(f.count(Kind::ButtonDown, 1) == 1 && f.count(Kind::ButtonDown, 4) == 0);
    for (const Event &e : f.events) {
      if (e.kind == Kind::ButtonDown) { assert(e.x == 500 && e.y == 300); }
    }
    assert(f.mouse.state().x == 560); /* Movement has no double-tap delay or interpolation tail. */
  }
  {
    Fixture f;
    f.down({17, 750, 350}); f.mouse.pointer_down(40, 850, 350, 1010);
    f.mouse.pointer_up(40, 1100, false); f.mouse.pointer_up(17, 1110, true);
    f.mouse.tick(3000);
    assert(f.count(Kind::ButtonDown, 4) == 1 && f.count(Kind::ButtonDown, 1) == 0);
  }
  {
    Fixture f;
    f.down({17, 750, 350}); f.mouse.pointer_down(40, 850, 350, 1010);
    f.mouse.tick(1189); assert(f.mouse.state().held == 0);
    f.mouse.tick(1190); assert(f.mouse.state().held == 2);
    f.mouse.pointer_up(40, 1200, false);
    assert(f.mouse.state().held == 0 && f.count(Kind::ButtonUp, 2) == 1);
    Point p{17, 850, 450}; f.mouse.move(&p, 1);
    f.mouse.pointer_up(17, 1210, true); f.mouse.tick(3000);
    assert(f.mouse.state().x == 500 && f.mouse.state().y == 300);
    assert(f.count(Kind::ButtonDown) == 1);
  }
  {
    Fixture f;
    f.down({17, 750, 350}); f.mouse.pointer_down(40, 850, 350, 1010);
    Point points[] = {{40, 890, 370}, {17, 790, 370}};
    f.mouse.move(points, 2);
    assert(f.mouse.state().held == 2 && f.mouse.state().x == 540 && f.mouse.state().y == 320);
    assert(f.count(Kind::Wheel) == 0);
    f.mouse.pointer_down(99, 950, 370, 1100);
    assert(f.mouse.state().held == 0 && f.count(Kind::ButtonUp, 2) == 1);
    Point scroll[] = {{99, 950, 434}, {40, 890, 434}, {17, 790, 434}};
    f.mouse.move(scroll, 3);
    assert(f.count(Kind::Wheel) == 2 && f.mouse.state().y == 320);
    f.mouse.pointer_up(99, 1120, false);
    scroll[1].y += 100; scroll[2].y += 100; f.mouse.move(scroll + 1, 2);
    assert(f.count(Kind::Wheel) == 2 && f.count(Kind::ButtonDown) == 1);
    f.mouse.pointer_up(40, 1140, false); f.mouse.pointer_up(17, 1150, true);
  }
  {
    Fixture f;
    f.down({17, 750, 350}); f.up(); f.mouse.cancel(); f.mouse.tick(3000);
    assert(f.count(Kind::ButtonDown) == 0);
    f.down({17, 750, 350}); f.mouse.pointer_down(40, 850, 350, f.time);
    f.mouse.tick(f.time + 180); assert(f.mouse.state().held == 2);
    f.mouse.cancel(true);
    assert(f.mouse.state().held == 0 && f.count(Kind::ButtonUp, 2) == 1);
    f.mouse.pointer_up(17, f.time + 300, true); f.mouse.tick(4000);
    assert(f.count(Kind::ButtonDown, 1) == 0 && f.count(Kind::ButtonDown, 4) == 0);
  }
  {
    std::vector<Event> events;
    EventQueue queue([&](const Event &event) { events.push_back(event); });
    for (int i = 0; i < 10000; i++) { queue.push({Kind::Motion, i, i}); }
    assert(events.empty());
    queue.flush();
    assert(events.size() == 1 && events[0].x == 9999);
    queue.push({Kind::Motion, 10, 20});
    queue.push({Kind::ButtonDown, 10, 20, 1});
    assert(events.size() == 3 && events[1].kind == Kind::Motion &&
           events[2].kind == Kind::ButtonDown && events[1].x == 10);
    for (int i = 0; i < 20; i++) { queue.push({Kind::Motion, 20 + i, 20}); }
    assert(events.size() == 23); /* Held-button painting/dragging samples are never coalesced. */
    queue.push({Kind::ButtonUp, 39, 20, 1});
    queue.push({Kind::Motion, 50, 60});
    queue.push({Kind::Wheel, 50, 60, 0, -1});
    assert(events.size() == 26 && events[24].kind == Kind::Motion &&
           events[25].kind == Kind::Wheel && events[24].x == 50);
    queue.flush(); assert(events.size() == 26);
  }
  {
    Fixture f;
    f.down({17, 700, 350});
    f.mouse.pointer_down(41, 800, 350, 1010);
    f.mouse.pointer_down(93, 900, 350, 1020);
    Point down[] = {{93, 900, 390}, {17, 700, 390}, {41, 800, 390}};
    f.mouse.move(down, 3);
    assert(f.count(Kind::Wheel) == 1 && f.events.back().delta == 1);
    for (Point &p : down) { p.y -= 80; }
    f.mouse.move(down, 3);
    assert(f.count(Kind::Wheel) == 3 && f.events.back().delta == -1);
    assert(f.count(Kind::ButtonDown) == 0 && f.mouse.state().y == 300);
  }
  {
    Fixture f;
    f.down({17, 700, 350}); f.mouse.pointer_down(41, 800, 350, 1010);
    Point pads[] = {{17, 740, 350}, {41, 840, 350}};
    f.mouse.move(pads, 2); assert(f.mouse.state().held == 2);
    Point button = f.control(Left, 99);
    f.mouse.pointer_down(button.id, button.x, button.y, 1100);
    assert(f.mouse.state().held == 1 && f.count(Kind::ButtonUp, 2) == 1);
    assert(f.events.back().kind == Kind::ButtonDown && f.events.back().button == 1);
    f.mouse.pointer_up(41, 1120, false);
    pads[0].x += 30; f.mouse.move(pads, 1);
    assert(f.mouse.state().held == 1 && f.mouse.state().x == 570);
    f.mouse.pointer_up(99, 1140, false); f.mouse.pointer_up(17, 1150, true);
    assert(f.mouse.state().held == 0 && f.count(Kind::ButtonUp, 1) == 1);
  }
  std::cout << "Virtual mouse: gesture clicks, middle drag, three-finger wheel, lifecycle, "
               "keyboard and bounded hover queue passed\n";
}
