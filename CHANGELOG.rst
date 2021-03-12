2.0.2
=====
*  Fixed compatibility with `icontract` >=2.4.0 (#24)

2.0.1
=====
* Updated asttokens dependency range to >=2,<3 since it conflicted with icontract>=2.3.0

2.0.0
=====
* Updated to icontract 2.0.0

1.4.0
=====
* Added errors to contract rendering

1.3.1
=====
* Updated to icontract 1.7.1 due to tight coupling with refactored icontract internals

1.3.0
=====
* Renders ``icontract.snapshot`` decorators

1.2.0
=====
* Made inferrence of implications more sophisticated

1.1.1
=====
* Updated to icontract 1.5.9

1.1.0
=====
* Added rendering of implications (not A or B is rendered as A ⇒ B)
* Contracts of property getter, setter and deleter are included in the documentation.

1.0.1
=====
* Fixed Readme to render correctly on pypi.org

1.0.0
=====
* Initial version
