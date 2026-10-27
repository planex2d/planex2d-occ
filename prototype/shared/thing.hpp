// SPDX-FileCopyrightText: 2026 Sebastian Hirnschall
// SPDX-License-Identifier: LGPL-2.1-or-later

#pragma once

#include <vector>

namespace prototype {

    // stands for a planex object: the core module binds it, the OCC module reads it through pybind11's conduit and
    // makes new ones that the core takes over
    struct Thing {
        std::vector<double> xs;
        double scale = 1.0;

        double Sum() const {
            double s = 0.0;
            for (double x : xs)
                s += x;
            return s * scale;
        }
    };

}
