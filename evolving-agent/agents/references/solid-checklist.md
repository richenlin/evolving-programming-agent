# SOLID 原则检查清单

代码审查时，使用此清单识别架构级问题和代码气味。

---

## SRP - 单一职责原则 (Single Responsibility Principle)

**定义**: 一个类/模块应该只有一个引起它变化的原因。

### 识别问题

- [ ] **多职责类**: 类是否处理了多个不相关的功能？
  - 示例：`UserService` 同时处理用户认证、邮件发送、日志记录
  - 反模式：构造函数参数过多（> 5 个）通常暗示多职责
  
- [ ] **上帝类**: 类的行数是否超过 300 行？方法数是否超过 20 个？
  
- [ ] **变更频率不同**: 类中是否有部分方法很少变化，而另一部分频繁变化？
  - 示例：`OrderProcessor` 中 `calculateTax()` 因政策频繁变化，但 `sendEmail()` 不变

### 重构建议

```python
# ❌ 违反 SRP
class UserAuth:
    def login(self, user, password): ...
    def send_email(self, user, message): ...  # 不相关职责
    def log_activity(self, user, action): ...  # 不相关职责

# ✅ 符合 SRP
class UserAuth:
    def login(self, user, password): ...

class EmailService:
    def send(self, user, message): ...

class ActivityLogger:
    def log(self, user, action): ...
```

---

## OCP - 开闭原则 (Open-Closed Principle)

**定义**: 软件实体应该对扩展开放，对修改关闭。

### 识别问题

- [ ] **频繁 switch/if-elif**: 是否使用类型判断而非多态？
  ```python
  # ❌ 违反 OCP
  def calculate_area(shape):
      if shape.type == 'circle':
          return 3.14 * shape.radius ** 2
      elif shape.type == 'rectangle':
          return shape.width * shape.height
  ```

- [ ] **硬编码策略**: 算法/策略是否直接写在代码中而非可配置？
  
- [ ] **新增类型需修改现有代码**: 添加新类型时是否需要修改现有函数？

### 重构建议

```python
# ✅ 符合 OCP
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def calculate_area(self): ...

class Circle(Shape):
    def calculate_area(self):
        return 3.14 * self.radius ** 2

class Rectangle(Shape):
    def calculate_area(self):
        return self.width * self.height
```

---

## LSP - 里氏替换原则 (Liskov Substitution Principle)

**定义**: 子类对象应该能够替换父类对象而不影响程序正确性。

### 识别问题

- [ ] **违反契约**: 子类是否改变了父类方法的行为预期？
  - 示例：父类 `Bird.fly()` 返回距离，子类 `Penguin.fly()` 抛出异常
  
- [ ] **前置条件加强**: 子类是否要求比父类更严格的输入？
  ```python
  # ❌ 违反 LSP
  class Parent:
      def process(self, value: int): ...  # 接受任意整数
  
  class Child(Parent):
      def process(self, value: int):
          if value < 0:
              raise ValueError()  # 加强了前置条件
  ```

- [ ] **后置条件减弱**: 子类是否返回比父类更弱的结果？
  
- [ ] **抛出意外异常**: 子类是否抛出父类不会抛出的异常？

### 重构建议

```python
# ❌ 违反 LSP
class Bird:
    def fly(self): return "flying"

class Penguin(Bird):
    def fly(self): raise Exception("Can't fly")  # 破坏契约

# ✅ 符合 LSP - 使用接口隔离
class FlyingBird(ABC):
    @abstractmethod
    def fly(self): ...

class Sparrow(FlyingBird):
    def fly(self): return "flying"

class Penguin:  # 不继承 FlyingBird
    pass
```

---

## ISP - 接口隔离原则 (Interface Segregation Principle)

**定义**: 客户端不应该依赖它不使用的接口。

### 识别问题

- [ ] **胖接口**: 接口是否包含多个不相关的方法？
  - 示例：`IWorker` 同时有 `work()` 和 `eat()`，但 `Robot` 不需要 `eat()`
  
- [ ] **空实现**: 类是否被迫实现它不需要的方法？
  ```python
  # ❌ 违反 ISP
  class Worker(ABC):
      @abstractmethod
      def work(self): ...
      @abstractmethod
      def eat(self): ...  # Robot 不需要
  
  class Robot(Worker):
      def work(self): ...
      def eat(self): pass  # 被迫空实现
  ```

- [ ] **接口方法过多**: 接口方法数是否超过 10 个？

### 重构建议

```python
# ✅ 符合 ISP
class Workable(ABC):
    @abstractmethod
    def work(self): ...

class Feedable(ABC):
    @abstractmethod
    def eat(self): ...

class Human(Workable, Feedable):
    def work(self): ...
    def eat(self): ...

class Robot(Workable):
    def work(self): ...
```

---

## DIP - 依赖倒置原则 (Dependency Inversion Principle)

**定义**: 高层模块不应该依赖低层模块，两者都应该依赖抽象。

### 识别问题

- [ ] **直接依赖具体类**: 高层模块是否直接创建低层实例？
  ```python
  # ❌ 违反 DIP
  class UserService:
      def __init__(self):
          self.db = MySQLDatabase()  # 直接依赖具体实现
          self.logger = FileLogger()  # 直接依赖具体实现
  ```

- [ ] **硬编码依赖**: 是否在代码中硬编码了依赖的类型？
  
- [ ] **测试困难**: 单元测试时是否难以 mock 依赖？

### 重构建议

```python
# ✅ 符合 DIP
from abc import ABC, abstractmethod

class IDatabase(ABC):
    @abstractmethod
    def save(self, entity): ...

class ILogger(ABC):
    @abstractmethod
    def log(self, message): ...

class UserService:
    def __init__(self, db: IDatabase, logger: ILogger):
        self.db = db
        self.logger = logger
```

---

## 常见代码气味 (Code Smells)

### Long Method (长方法)

- [ ] 方法行数 > 50 行
- [ ] 方法包含多个抽象层次
- [ ] 方法名包含 "and" 或 "or"

**重构**: Extract Method

### Feature Envy (特性嫉妒)

- [ ] 方法是否频繁访问另一个类的数据？
  ```python
  # ❌ Feature Envy
  class Order:
      def calculate_discount(self, customer):
          return customer.base_discount * customer.loyalty_factor
  ```

**重构**: Move Method 到被嫉妒的类

### Data Clumps (数据泥团)

- [ ] 是否有 3 个或更多字段总是同时出现？
  - 示例：`street`, `city`, `zip` 在多个类中重复

**重构**: Extract Class (如 `Address`)

### Primitive Obsession (基本类型偏执)

- [ ] 是否使用基本类型表示领域概念？
  - 示例：用 `str` 表示电话号码、邮箱、金额

**重构**: 使用值对象 (Value Object)

### Shotgun Surgery (霰弹式修改)

- [ ] 一个变更是否需要修改多个类？
  
**重构**: 内联相关逻辑到一个类中

### Divergent Change (发散式变化)

- [ ] 一个类是否因多种不同原因被修改？
  
**重构**: Extract Class 按 change reason 分离

---

## 重构启发式规则

1. **何时拆分类**:
   - 类职责 > 1 个
   - 构造函数参数 > 5 个
   - 类行数 > 300 行
   - 测试时需要 mock > 3 个依赖

2. **何时引入抽象**:
   - 有 2 个以上相似实现
   - 需要支持未来扩展（OCP）
   - 需要解耦高层与低层（DIP）

3. **何时提取方法**:
   - 方法行数 > 10 行
   - 需要注释解释代码块
   - 代码块可复用

4. **何时使用多态替代条件**:
   - `switch` 或 `if-elif` 基于类型
   - 每次新增类型需修改条件逻辑

---

## 审查输出格式

发现 SOLID 违反时，按以下格式记录：

```markdown
[P2] file.py:42 - 违反 SRP: `UserService` 同时处理认证、邮件、日志
建议: 拆分为 `AuthService`, `EmailService`, `ActivityLogger`

[P1] order.py:128 - 违反 OCP: 使用 switch 判断形状类型计算面积
建议: 引入 Shape 抽象类，使用多态替代 switch
```

---

## 参考资料

- Martin Fowler, "Refactoring: Improving the Design of Existing Code"
- Robert C. Martin, "Clean Architecture"
- [SOLID 原则详解](https://en.wikipedia.org/wiki/SOLID)
